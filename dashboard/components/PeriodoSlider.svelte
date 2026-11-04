<!--
  Slider de período com duas alças. Recebe a lista de meses ('AAAA-MM', em ordem crescente)
  e grava inputs.inicio e inputs.fim no mesmo formato dos Dropdowns de antes
  ({ value: 'AAAA-MM' }), então o SQL das páginas continua o mesmo.
  Uso: <PeriodoSlider data={meses_crescente} padrao={inicio_padrao[0]?.mes} />
-->
<script>
	import { QueryLoad } from '@evidence-dev/core-components';
	import { Query } from '@evidence-dev/sdk/usql';
	import PeriodoFaixa from './PeriodoFaixa.svelte';

	export let data;
	/** Mês inicial ('AAAA-MM'); sem ele, começa no primeiro mês da série */
	export let padrao = undefined;
</script>

<QueryLoad {data} let:loaded>
	<span slot="skeleton" class="text-base-content-muted text-sm">Carregando período…</span>
	<PeriodoFaixa
		meses={(Query.isQuery(loaded) ? Array.from(loaded) : loaded ?? []).map((r) => r.mes)}
		{padrao}
	/>
</QueryLoad>
