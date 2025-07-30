from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

import httpx
import structlog
from docstring_parser import parse
from langchain_core.tools import StructuredTool
from structlog.stdlib import AsyncBoundLogger

from lib.core.langchain_tools import create_pydantic_model_from_function

if TYPE_CHECKING:
    from lib.core.chat_agent import ChatAgent


class CalClient:
    """
    Async client for interacting with the Cal.com API.
    """

    def __init__(
        self,
        api_key: str,
        default_event_type_id: int = 1,
        base_url: str = "https://api.cal.com/v2",
        logger: structlog.stdlib.AsyncBoundLogger | None = None,
    ) -> None:
        """
        Initializes the Cal.com client.

        Args:
            api_key: The Cal.com API key.
            default_event_type_id: The default event type ID for bookings.
            base_url: The base URL for the Cal.com API.
            logger: A structlog logger for structured logging.
        """
        self.api_key = api_key
        self.default_event_type_id = default_event_type_id
        self.base_url = base_url
        self.logger = logger or structlog.get_logger(__name__)

    async def _request(
        self,
        method: str,
        endpoint: str,
        logger: AsyncBoundLogger,
        **kwargs: Any,
    ) -> httpx.Response | dict[str, Any]:
        """
        Makes an authenticated request to the Cal.com API.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "cal-api-version": "2024-08-13",
            "Content-Type": "application/json",
        }

        await logger.info(
            "Making Cal.com API request",
            method=method,
            url=url,
            params=kwargs.get("params"),
        )

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=headers, **kwargs
            )
            await logger.info(
                "Received Cal.com API response",
                status_code=response.status_code,
            )
            if response.status_code != 200:
                await logger.error(
                    "Cal.com API request failed",
                    status_code=response.status_code,
                    response_text=response.text,
                )
                error_data = response.json()
                return cast(dict[str, Any], error_data)
            return response

    async def create_booking(
        self,
        start: str,
        attendee_name: str,
        attendee_email: str,
        attendee_timezone: str,
        logger: AsyncBoundLogger,
        guests: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        length_in_minutes: int | None = None,
    ) -> dict[str, Any]:
        """
        Creates a new booking on Cal.com.

        Args:
            start: The start time in ISO 8601 format (UTC).
            attendee_name: The name of the person booking the event.
            attendee_email: The email of the person booking the event.
            attendee_timezone: The IANA time zone of the attendee.
            logger: The request-specific logger.
            guests: An optional list of guest emails.
            metadata: Optional metadata for the booking.
            length_in_minutes: Optional duration for variable length events.

        Returns:
            A dictionary containing the created booking's details.
        """
        endpoint = "bookings"
        payload: dict[str, Any] = {
            "start": start,
            "eventTypeId": self.default_event_type_id,
            "attendee": {
                "language": "en",
                "name": attendee_name,
                "email": attendee_email,
                "timeZone": attendee_timezone,
            },
            "location": {"type": "integration", "integration": "cal-video"},
            "bookingFieldsResponses": {"notes": "Agentic schedule"},
        }

        if guests:
            payload["guests"] = guests
        if metadata:
            payload["metadata"] = metadata
        if length_in_minutes:
            payload["lengthInMinutes"] = length_in_minutes

        await logger.info("Creating Cal.com booking", payload=payload)
        response = await self._request(
            "POST", endpoint, logger=logger, json=payload
        )
        if isinstance(response, dict):
            return response

        json_response = cast(dict[str, Any], response.json())
        await logger.info(
            "Successfully created booking",
            booking_uid=json_response.get("data", {}).get("uid"),
        )
        return json_response

    async def get_bookings(
        self,
        logger: AsyncBoundLogger,
        attendee_email: str | None = None,
        after_start: str | None = None,
        before_end: str | None = None,
        status: list[str] | None = None,
        take: int = 100,
        skip: int = 0,
    ) -> dict[str, Any]:
        """
        Fetches a list of bookings, with optional filters and pagination.

        Args:
            logger: The request-specific logger.
            attendee_email: Filter bookings by the attendee's email address.
            after_start: Filter for bookings starting after this ISO 8601 date.
            before_end: Filter for bookings ending before this ISO 8601 date.
            status: Filter bookings by status (e.g., ['accepted', 'pending']).
            take: The number of items to return.
            skip: The number of items to skip for pagination.

        Returns:
            A dictionary containing the list of bookings and pagination info.
        """
        endpoint = "bookings"
        params: dict[str, Any] = {"take": take, "skip": skip}

        if attendee_email:
            params["attendeeEmail"] = attendee_email
        if after_start:
            params["afterStart"] = after_start
        if before_end:
            params["beforeEnd"] = before_end
        if status:
            params["status"] = ",".join(status)
        else:
            # Default to showing upcoming and unconfirmed bookings
            params["status"] = ",".join(["upcoming", "unconfirmed"])

        await logger.info("Fetching Cal.com bookings", params=params)
        response = await self._request(
            "GET", endpoint, logger=logger, params=params
        )
        if isinstance(response, dict):
            return response

        json_response = cast(dict[str, Any], response.json())
        await logger.info(
            "Successfully fetched bookings",
            count=len(json_response.get("data", [])),
        )
        return json_response

    async def get_booking(
        self, booking_uid: str, logger: AsyncBoundLogger
    ) -> dict[str, Any]:
        """
        Fetches a single booking by its UID.

        Args:
            booking_uid: The unique identifier (UID) of the booking.
            logger: The request-specific logger.

        Returns:
            A dictionary containing the booking's details.
        """
        endpoint = f"bookings/{booking_uid}"
        await logger.info(
            "Fetching Cal.com booking by UID", booking_uid=booking_uid
        )
        response = await self._request("GET", endpoint, logger=logger)
        if isinstance(response, dict):
            return response

        json_response = cast(dict[str, Any], response.json())
        await logger.info(
            "Successfully fetched single booking", booking_uid=booking_uid
        )
        return json_response

    async def cancel_booking(
        self,
        booking_uid: str,
        logger: AsyncBoundLogger,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancels a booking by its UID.

        Args:
            booking_uid: The unique identifier (UID) of the booking to cancel.
            logger: The request-specific logger.
            reason: An optional reason for the cancellation.

        Returns:
            A dictionary containing the details of the cancelled booking.
        """
        endpoint = f"bookings/{booking_uid}/cancel"
        payload = {}
        if reason:
            payload["cancellationReason"] = reason

        await logger.info(
            "Cancelling Cal.com booking",
            booking_uid=booking_uid,
            reason=reason,
        )
        response = await self._request(
            "POST", endpoint, logger=logger, json=payload
        )
        if isinstance(response, dict):
            return response

        json_response = cast(dict[str, Any], response.json())
        await logger.info(
            "Successfully cancelled booking", booking_uid=booking_uid
        )
        return json_response

    async def cancel_all_bookings(
        self, logger: AsyncBoundLogger, reason: str | None = None
    ) -> dict[str, Any]:
        """
        Fetches and cancels all active (accepted or pending) bookings.

        This is a client-side convenience method that iterates through all
        active bookings and cancels them one by one.

        Args:
            logger: The request-specific logger.
            reason: An optional reason for the cancellation.

        Returns:
            A dictionary summarizing the operation, including a success count
            and a list of any failures.
        """
        await logger.info("Starting to cancel all active bookings.")
        active_bookings_response = await self.get_bookings(
            logger=logger, status=["upcoming", "unconfirmed"]
        )

        if "error" in active_bookings_response:
            await logger.error(
                "Failed to fetch active bookings to cancel.",
                error=active_bookings_response["error"],
            )
            return {
                "cancelled_count": 0,
                "failures": ["Failed to fetch bookings."],
            }

        bookings_to_cancel = active_bookings_response.get("data", [])
        if not bookings_to_cancel:
            await logger.info("No active bookings found to cancel.")
            return {"cancelled_count": 0, "failures": []}

        success_count = 0
        failures = []

        for booking in bookings_to_cancel:
            booking_uid = booking.get("uid")
            if not booking_uid:
                continue

            await logger.info(
                "Cancelling booking as part of bulk operation",
                booking_uid=booking_uid,
            )

            cancellation_result = await self.cancel_booking(
                booking_uid=booking_uid, reason=reason, logger=logger
            )
            if "error" in cancellation_result:
                failure_detail = {
                    "booking_uid": booking_uid,
                    "error": cancellation_result["error"],
                }
                failures.append(failure_detail)
                await logger.error(
                    "Failed during bulk cancellation.", **failure_detail
                )
            else:
                success_count += 1

        summary = {"cancelled_count": success_count, "failures": failures}
        await logger.info("Finished bulk cancellation.", **summary)
        return summary

    async def reschedule_booking(
        self,
        booking_uid: str,
        start: str,
        logger: AsyncBoundLogger,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Reschedules a booking to a new start time.

        Args:
            booking_uid: The unique identifier of the booking to reschedule.
            start: The new start time in ISO 8601 format (UTC).
            logger: The request-specific logger.
            reason: An optional reason for the reschedule.

        Returns:
            A dictionary containing the details of the rescheduled booking.
        """
        endpoint = f"bookings/{booking_uid}/reschedule"
        payload: dict[str, Any] = {"start": start}
        if reason:
            payload["reschedulingReason"] = reason

        await logger.info(
            "Rescheduling Cal.com booking",
            booking_uid=booking_uid,
            payload=payload,
        )
        response = await self._request(
            "POST", endpoint, logger=logger, json=payload
        )
        if isinstance(response, dict):
            return response

        json_response = cast(dict[str, Any], response.json())
        await logger.info(
            "Successfully rescheduled booking", booking_uid=booking_uid
        )
        return json_response

    def get_tool_callables(self) -> list[Callable[..., Any]]:
        """
        Returns a list of its methods that are intended to be used as tools.
        """
        return [
            self.create_booking,
            self.get_bookings,
            self.cancel_booking,
            self.reschedule_booking,
            self.cancel_all_bookings,
        ]

    def get_tools(
        self, agent: "ChatAgent", logger: AsyncBoundLogger
    ) -> list[StructuredTool]:
        """
        Builds and returns a list of LangChain StructuredTools from this
        client.
        """
        tools = []
        for func in self.get_tool_callables():
            docstring = parse(func.__doc__ or "")
            description = docstring.short_description or ""
            tool_name = func.__name__
            model_name = f"{tool_name.title().replace('_', '')}Args"

            def create_tool_wrapper(
                agent: "ChatAgent", tool_name: str, logger: AsyncBoundLogger
            ) -> Callable[..., Any]:
                async def tool_wrapper(**kwargs: Any) -> str:
                    return await agent._run_tool(
                        tool_name=tool_name, logger=logger, **kwargs
                    )

                return tool_wrapper

            tool = StructuredTool(
                name=tool_name,
                coroutine=create_tool_wrapper(agent, tool_name, logger),
                description=description,
                args_schema=create_pydantic_model_from_function(
                    func, model_name=model_name
                ),
            )
            tools.append(tool)
        return tools
