<script lang="ts">
	import { onMount } from 'svelte';
	import { PUBLIC_API_BASE_URL } from '$env/static/public';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';
	import * as Avatar from '$lib/components/ui/avatar';
	import { Label } from '$lib/components/ui/label';
	import { marked } from 'marked';

	type Message = {
		role: 'user' | 'agent';
		text: string;
	};

	let messages: Message[] = $state([]);
	let inputValue = $state('');
	let sessionId: string | null = $state(null);
	let isLoading = $state(false);

	onMount(() => {
		messages = [{ role: 'agent', text: 'Hello! How can I help you manage your schedule today?' }];
	});

	async function parseMarkdown(text: string): Promise<string> {
		return await marked.parse(text);
	}

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!inputValue.trim() || isLoading) return;

		const userMessage = inputValue;
		messages = [...messages, { role: 'user', text: userMessage }];
		inputValue = '';
		isLoading = true;

		try {
			const response = await fetch(`${PUBLIC_API_BASE_URL}/api/v1/chat/message`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					message: userMessage,
					session_id: sessionId
				})
			});

			if (!response.ok) {
				throw new Error('Network response was not ok');
			}

			const data = await response.json();
			messages = [...messages, { role: 'agent', text: data.response }];
			sessionId = data.session_id;

		} catch (error) {
			console.error('Failed to send message:', error);
			messages = [...messages, { role: 'agent', text: 'Sorry, I encountered an error. Please try again.' }];
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="flex h-screen w-full items-center justify-center bg-background p-4">
	<Card.Root class="w-full max-w-2xl h-full flex flex-col">
		<Card.Header>
			<Card.Title class="text-2xl">Cal.com Agent</Card.Title>
			<Card.Description>Your AI-powered scheduling assistant.</Card.Description>
		</Card.Header>
		<Card.Content class="flex-1 overflow-y-auto p-6 space-y-4">
			{#each messages as message}
				<div class="flex items-start gap-4 {message.role === 'user' ? 'justify-end' : ''}">
					{#if message.role === 'agent'}
						<Avatar.Root class="h-9 w-9">
							<Avatar.Image src="/favicon.svg" alt="Agent" />
							<Avatar.Fallback>A</Avatar.Fallback>
						</Avatar.Root>
					{/if}
					<div
						class="rounded-lg p-3 text-sm {message.role === 'user'
							? 'bg-primary text-primary-foreground'
							: 'bg-muted'}"
					>
						{#await parseMarkdown(message.text)}
							<p>...</p>
						{:then html}
													{#if message.role === 'agent'}
							<div class="prose dark:prose-invert max-w-none prose-p:mb-6 prose-ul:space-y-4 prose-li:mb-3 prose-a:text-blue-600 prose-a:underline hover:prose-a:text-blue-800">
								{@html html}
							</div>
						{:else}
							<p>{message.text}</p>
						{/if}
						{/await}
					</div>
					{#if message.role === 'user'}
						<Avatar.Root class="h-9 w-9">
							<Avatar.Fallback>U</Avatar.Fallback>
						</Avatar.Root>
					{/if}
				</div>
			{/each}
			{#if isLoading}
				<div class="flex items-start gap-4">
					<Avatar.Root class="h-9 w-9">
						<Avatar.Image src="/favicon.svg" alt="Agent" />
						<Avatar.Fallback>A</Avatar.Fallback>
					</Avatar.Root>
					<div class="rounded-lg p-3 text-sm bg-muted">
						<p class="animate-pulse">...</p>
					</div>
				</div>
			{/if}
		</Card.Content>
		<Card.Footer>
			<form onsubmit={handleSubmit} class="flex w-full items-center space-x-2">
				<Input
					id="message"
					placeholder="Ask me to book, cancel, or show your meetings..."
					class="flex-1"
					autocomplete="off"
					bind:value={inputValue}
					disabled={isLoading}
				/>
				<Button type="submit" disabled={isLoading}>
					{#if isLoading}
						<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Sending...
					{:else}
						Send
					{/if}
				</Button>
			</form>
		</Card.Footer>
	</Card.Root>
</div>
