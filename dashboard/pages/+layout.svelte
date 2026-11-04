<script>
	// Mesmas importações do layout padrão do Evidence: sem elas o site perde o Tailwind
	import '@evidence-dev/tailwind/fonts.css';
	import '../app.css';
	import { EvidenceDefaultLayout } from '@evidence-dev/core-components';
	import { onMount } from 'svelte';
	export let data;

	// Botão de tema: o Evidence observa html[data-theme] e guarda a escolha
	let tema = 'light';
	onMount(() => {
		const html = document.documentElement;
		const ler = () => (tema = html.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');
		ler();
		const obs = new MutationObserver(ler);
		obs.observe(html, { attributeFilter: ['data-theme'] });
		return () => obs.disconnect();
	});
	function trocarTema() {
		document.documentElement.setAttribute('data-theme', tema === 'dark' ? 'light' : 'dark');
	}
</script>

<svelte:head>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		rel="stylesheet"
		href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap"
	/>
</svelte:head>

<EvidenceDefaultLayout
	{data}
	title="Vendas de Veículos no Brasil"
	homePageName="Visão geral"
	githubRepo="https://github.com/vitorsarilio/vendas-veiculos-brasil"
	neverShowQueries={false}
	maxWidth={1280}
>
	<slot slot="content" />
</EvidenceDefaultLayout>

<button
	class="botao-tema"
	on:click={trocarTema}
	aria-label={tema === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'}
>
	{#if tema === 'dark'}
		<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="4.5" fill="currentColor" /><g stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8" /></g></svg>
		<span>Claro</span>
	{:else}
		<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" fill="currentColor" /></svg>
		<span>Escuro</span>
	{/if}
</button>

<style>
	.botao-tema {
		position: fixed;
		right: 1.25rem;
		bottom: 1.25rem;
		z-index: 50;
		display: flex;
		align-items: center;
		gap: 0.45rem;
		padding: 0.55rem 0.95rem;
		border-radius: 999px;
		border: 1px solid var(--base-300);
		background: var(--base-100);
		color: var(--base-heading);
		font-size: 0.85rem;
		font-weight: 600;
		box-shadow: 0 6px 20px rgb(0 0 0 / 0.18);
		cursor: pointer;
		transition: transform 0.15s ease;
	}
	.botao-tema:hover {
		transform: translateY(-1px);
		border-color: var(--primary);
	}
	.botao-tema:focus-visible {
		outline: 2px solid var(--primary);
		outline-offset: 3px;
	}

	/* Archivo expandida nos títulos e números grandes; Inter no resto */
	:global(article h1),
	:global(article h2),
	:global(.kpis .valor-grande) {
		font-family: 'Archivo', 'Inter', sans-serif;
		font-stretch: 115%;
		letter-spacing: -0.01em;
	}
	:global(article h1) {
		font-weight: 800;
		font-size: 2.1rem;
		line-height: 1.1;
		margin-bottom: 0.4rem;
	}
	:global(article h2) {
		font-weight: 700;
		font-size: 1.35rem;
		margin-top: 2.4rem;
	}

	/* Indicadores em cartões, cada um com a sua cor no topo */
	:global(.kpis) {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
		gap: 0.75rem;
		margin: 1rem 0 1.5rem;
	}
	:global(.kpis > div) {
		display: block !important;
		margin: 0 !important;
		padding: 1rem 1.1rem 0.9rem !important;
		border-radius: 14px;
		background: var(--base-200);
		border: 1px solid var(--base-300);
		border-top: 3px solid var(--primary);
	}
	:global(.kpis > div:nth-child(2)) {
		border-top-color: var(--accent);
	}
	:global(.kpis > div:nth-child(3)) {
		border-top-color: var(--info);
	}
	:global(.kpis > div:nth-child(4)) {
		border-top-color: var(--warning);
	}
	:global(.kpis .valor-grande) {
		font-size: 2rem !important;
		font-weight: 750 !important;
		color: var(--base-heading);
		font-variant-numeric: tabular-nums;
		line-height: 1.15;
	}
	:global(.kpis .titulo-kpi) {
		font-size: 0.8rem;
		color: var(--base-content-muted);
	}

	:global(article table) {
		font-variant-numeric: tabular-nums;
	}
</style>
