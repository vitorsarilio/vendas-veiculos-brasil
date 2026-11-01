from pathlib import Path

import pytest
import requests

from ingestao import relatorios
from ingestao.rede import NaoEPdf, baixar_pdf
from ingestao.relatorios import Relatorio, corrigir_lista, escolher_um_por_mes

PDF = b"%PDF-1.4 conteudo"
HTML_404 = b"<!DOCTYPE html><html>Pagina nao encontrada</html>"


class RespostaFalsa:
    def __init__(self, status=200, corpo=b"", json_=None):
        self.status_code, self.corpo, self._json = status, corpo, json_

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def iter_content(self, _tamanho):
        yield self.corpo

    def json(self):
        return self._json

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class SessaoFalsa:
    def __init__(self, arquivos: dict[str, RespostaFalsa], listas: dict[str, list] | None = None):
        self.arquivos, self.listas, self.pedidos = arquivos, listas or {}, []

    def get(self, url, **_):
        self.pedidos.append(url)
        return self.arquivos.get(url.rsplit("/", 1)[-1], RespostaFalsa(404, HTML_404))

    def post(self, _url, data, **_):
        return RespostaFalsa(json_={"data": {"blocos": self.listas.get(data["ano"], [])}})


@pytest.fixture(autouse=True)
def sem_pausa(monkeypatch):
    monkeypatch.setattr(relatorios.time, "sleep", lambda _s: None)


def test_versao_pelo_contador_do_nome():
    assert Relatorio("2019-06", "2_2019_06_2.pdf").versao == 2
    assert Relatorio("2019-06", "2019_06_2.pdf").versao == 1
    assert Relatorio("2012-12", "6_2012_12_2.pdf").versao == 6


def test_duplicata_fica_com_a_versao_maior():
    escolhidos, descartados = escolher_um_por_mes([
        Relatorio("2019-06", "2019_06_2.pdf"), Relatorio("2019-06", "2_2019_06_2.pdf"), Relatorio("2019-07", "2019_07_2.pdf"),
    ])
    assert [r.link for r in escolhidos] == ["2_2019_06_2.pdf", "2019_07_2.pdf"]
    assert descartados == [{"mes": "2019-06", "descartado": "2019_06_2.pdf", "usado": "2_2019_06_2.pdf"}]


def test_correcao_da_lista_oficial():
    # abr/2005: a lista aponta para o relatório de maio
    corrigidos = corrigir_lista([Relatorio("2005-04", "3_2005_05_2.pdf"), Relatorio("2005-05", "4_2005_05_2.pdf")])
    assert sorted((r.mes, r.link) for r in corrigidos) == [("2005-04", "3_2005_04_2.pdf"), ("2005-05", "4_2005_05_2.pdf")]


def test_lista_com_item_estranho_falha():
    sessao = SessaoFalsa({}, {"2003": [{"data": "sem data", "link": "x.pdf"}]})
    with pytest.raises(ValueError, match="Item inesperado"):
        relatorios.consultar_ano(sessao, 2003)


def test_pagina_html_no_lugar_do_pdf_nao_entra_no_cache(tmp_path: Path):
    sessao = SessaoFalsa({"x.pdf": RespostaFalsa(200, HTML_404)})
    with pytest.raises(NaoEPdf):
        baixar_pdf(sessao, "https://exemplo/x.pdf", tmp_path / "x.pdf")
    assert list(tmp_path.iterdir()) == []


def test_copia_local_baixa_o_que_falta_e_os_ultimos_meses(tmp_path: Path):
    lista = [Relatorio(f"2026-0{m}", f"2026_0{m}_02.pdf") for m in range(1, 6)]
    for rel in lista[:4]:  # jan a abr já estão no cache
        (tmp_path / rel.arquivo_local).write_bytes(PDF)
    sessao = SessaoFalsa({rel.link: RespostaFalsa(200, PDF) for rel in lista})
    situacao = relatorios.atualizar_copia_local(sessao, lista, tmp_path)
    assert [s["baixado_agora"] for s in situacao] == [False, False, False, True, True]  # abr e mai rebaixados
    assert all(len(s["sha256"]) == 64 for s in situacao)


def test_mes_sem_pdf_vira_erro_e_mes_com_copia_mantem_a_copia(tmp_path: Path):
    lista = [Relatorio("2026-08", "2026_08_02.pdf"), Relatorio("2026-09", "2026_09_02.pdf")]
    (tmp_path / lista[0].arquivo_local).write_bytes(PDF)
    situacao = relatorios.atualizar_copia_local(SessaoFalsa({}), lista, tmp_path)
    assert situacao[0]["baixado_agora"] is False and "sha256" in situacao[0]
    assert "erro" in situacao[1] and "sha256" not in situacao[1]
