import inspect
from collections.abc import Callable
from typing import Any, cast

from docstring_parser import parse
from pydantic import BaseModel, Field, create_model


def create_pydantic_model_from_function(
    func: Callable[..., Any],
    model_name: str,
) -> type[BaseModel]:
    """
    Dynamically creates a Pydantic model from a function's signature,
    including descriptions from the docstring.

    Args:
        func: The function to introspect.
        model_name: The desired name for the created Pydantic model.

    Returns:
        A Pydantic model class representing the function's arguments.
    """
    fields: dict[str, Any] = {}
    signature = inspect.signature(func)
    docstring = parse(func.__doc__ or "")
    doc_params = {
        param.arg_name: param.description for param in docstring.params
    }

    for param_name, parameter in signature.parameters.items():
        if param_name in ("self", "cls", "logger"):
            continue

        param_type = parameter.annotation
        default_value = parameter.default
        description = doc_params.get(param_name)

        if default_value is inspect.Parameter.empty:
            fields[param_name] = (
                param_type,
                Field(..., description=description),
            )
        else:
            fields[param_name] = (
                param_type,
                Field(default=default_value, description=description),
            )

    dynamic_model = create_model(model_name, **fields)
    return cast(type[BaseModel], dynamic_model)
