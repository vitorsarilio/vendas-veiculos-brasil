<script>
	import { getInputContext } from '@evidence-dev/sdk/utils/svelte';

	/** @type {string[]} meses em ordem crescente, 'AAAA-MM' */
	export let meses = [];
	export let padrao = undefined;

	const inputs = getInputContext();
	const NOMES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
	const rotulo = (m) => (m ? `${NOMES[Number(m.slice(5, 7)) - 1]}/${m.slice(0, 4)}` : '');

	let a = 0;
	let b = 0;
	let iniciado = false;
	$: ultimo = Math.max(meses.length - 1, 0);

	function gravar() {
		if (!meses.length) return;
		$inputs.inicio = { value: meses[a], label: rotulo(meses[a]) };
		$inputs.fim = { value: meses[b], label: rotulo(meses[b]) };
	}

	// Valor inicial gravado já na montagem, para as consultas da página rodarem com ele
	$: if (!iniciado && meses.length) {
		b = ultimo;
		const i = padrao ? meses.indexOf(padrao) : 0;
		a = i >= 0 ? i : 0;
		gravar();
		iniciado = true;
	}

	function moverInicio() {
		if (a > b) a = b;
	}
	function moverFim() {
		if (b < a) b = a;
	}

	function atalho(n) {
		b = ultimo;
		a = n ? Math.max(0, ultimo - n + 1) : 0;
		gravar();
	}

	$: pct = (i) => (ultimo ? (i / ultimo) * 100 : 0);
	$: qtd = b - a + 1;

	// Marcas de ano no trilho: um ano a cada 2 ou 4, conforme o tamanho da série
	$: anos = meses
		.map((m, i) => ({ m, i }))
		.filter(({ m }) => m.endsWith('-01'));
	$: passo = anos.length > 16 ? 4 : anos.length > 8 ? 2 : 1;
	$: marcas = anos.filter((_, k) => k % passo === 0);
</script>

{#if meses.length}
	<div class="periodo">
		<div class="topo">
			<div class="faixa-texto" aria-live="polite">
				<span class="mes">{rotulo(meses[a])}</span>
				<span class="seta" aria-hidden="true">→</span>
				<span class="mes">{rotulo(meses[b])}</span>
				<span class="dur">{qtd} {qtd === 1 ? 'mês' : 'meses'}</span>
			</div>
			<div class="atalhos" role="group" aria-label="Atalhos de período">
				<button class:ativo={a === Math.max(0, ultimo - 11) && b === ultimo} on:click={() => atalho(12)}>12 meses</button>
				<button class:ativo={a === Math.max(0, ultimo - 59) && b === ultimo} on:click={() => atalho(60)}>5 anos</button>
				<button class:ativo={a === 0 && b === ultimo} on:click={() => atalho(0)}>Tudo</button>
			</div>
		</div>

		<div class="trilho-area">
			<div class="trilho"></div>
			<div class="selecao" style="left:{pct(a)}%; right:{100 - pct(b)}%"></div>
			<input
				type="range"
				min="0"
				max={ultimo}
				step="1"
				bind:value={a}
				on:input={moverInicio}
				on:change={gravar}
				aria-label="Início do período"
				aria-valuetext={rotulo(meses[a])}
				style="z-index:{a >= ultimo - 1 ? 5 : 3}"
			/>
			<input
				type="range"
				min="0"
				max={ultimo}
				step="1"
				bind:value={b}
				on:input={moverFim}
				on:change={gravar}
				aria-label="Fim do período"
				aria-valuetext={rotulo(meses[b])}
				style="z-index:4"
			/>
		</div>

		<div class="anos" aria-hidden="true">
			{#each marcas as { m, i }}
				<span style="left:{pct(i)}%">{m.slice(0, 4)}</span>
			{/each}
		</div>
	</div>
{/if}

<style>
	.periodo {
		margin: 0.75rem 0 1.25rem;
		padding: 1rem 1.25rem 1.6rem;
		border-radius: 14px;
		background: var(--base-200);
		border: 1px solid var(--base-300);
	}
	.topo {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.9rem;
	}
	.faixa-texto {
		display: flex;
		align-items: baseline;
		gap: 0.5rem;
		font-variant-numeric: tabular-nums;
	}
	.mes {
		font-family: 'Archivo', sans-serif;
		font-stretch: 112%;
		font-weight: 700;
		font-size: 1.35rem;
		color: var(--base-heading);
	}
	.seta {
		color: var(--primary);
		font-weight: 700;
	}
	.dur {
		margin-left: 0.4rem;
		font-size: 0.8rem;
		color: var(--base-content-muted);
	}
	.atalhos {
		display: flex;
		gap: 0.35rem;
	}
	.atalhos button {
		font-size: 0.78rem;
		padding: 0.3rem 0.7rem;
		border-radius: 999px;
		border: 1px solid var(--base-300);
		color: var(--base-content);
		background: var(--base-100);
		cursor: pointer;
	}
	.atalhos button:hover {
		border-color: var(--primary);
	}
	.atalhos button.ativo {
		background: var(--primary);
		border-color: var(--primary);
		color: var(--primary-content);
	}
	.atalhos button:focus-visible {
		outline: 2px solid var(--primary);
		outline-offset: 2px;
	}

	.trilho-area {
		position: relative;
		height: 28px;
	}
	.trilho,
	.selecao {
		position: absolute;
		top: 50%;
		height: 6px;
		transform: translateY(-50%);
		border-radius: 999px;
	}
	.trilho {
		left: 0;
		right: 0;
		background: var(--base-300);
	}
	.selecao {
		background: linear-gradient(90deg, var(--primary), var(--accent));
	}
	input[type='range'] {
		position: absolute;
		inset: 0;
		width: 100%;
		margin: 0;
		background: none;
		pointer-events: none;
		-webkit-appearance: none;
		appearance: none;
	}
	input[type='range']::-webkit-slider-runnable-track {
		background: transparent;
		height: 28px;
	}
	input[type='range']::-moz-range-track {
		background: transparent;
	}
	input[type='range']::-webkit-slider-thumb {
		-webkit-appearance: none;
		pointer-events: auto;
		width: 22px;
		height: 22px;
		margin-top: 3px;
		border-radius: 50%;
		background: var(--base-100);
		border: 3px solid var(--primary);
		box-shadow: 0 2px 6px rgb(0 0 0 / 0.25);
		cursor: grab;
	}
	input[type='range']::-moz-range-thumb {
		pointer-events: auto;
		width: 16px;
		height: 16px;
		border-radius: 50%;
		background: var(--base-100);
		border: 3px solid var(--primary);
		box-shadow: 0 2px 6px rgb(0 0 0 / 0.25);
		cursor: grab;
	}
	input[type='range']:active::-webkit-slider-thumb {
		cursor: grabbing;
		transform: scale(1.12);
	}
	input[type='range']:focus-visible::-webkit-slider-thumb {
		outline: 3px solid color-mix(in srgb, var(--primary) 40%, transparent);
	}

	.anos {
		position: relative;
		height: 0.9rem;
		margin-top: 0.15rem;
	}
	.anos span {
		position: absolute;
		transform: translateX(-50%);
		font-size: 0.7rem;
		color: var(--base-content-muted);
		font-variant-numeric: tabular-nums;
	}
	@media (prefers-reduced-motion: reduce) {
		input[type='range']:active::-webkit-slider-thumb {
			transform: none;
		}
	}
</style>
