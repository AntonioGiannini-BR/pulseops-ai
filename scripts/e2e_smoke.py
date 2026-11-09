#!/usr/bin/env python3
"""E2E de navegador apenas contra a stack local DESCARTÁVEL do CI.

Requer: pip install playwright && python -m playwright install chromium
Variáveis: PULSEOPS_E2E_ALLOW_WRITE=TEST_ONLY_DISPOSABLE_DB,
PULSEOPS_E2E_PASSWORD e PULSEOPS_E2E_BASE_URL (opcional).
"""
import os
import re
import sys
import uuid
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main() -> int:
    base = os.environ.get("PULSEOPS_E2E_BASE_URL", "http://127.0.0.1:18080").rstrip("/")
    password = os.environ.get("PULSEOPS_E2E_PASSWORD", "")
    parsed = urlsplit(base)
    if (
        os.environ.get("PULSEOPS_E2E_ALLOW_WRITE") != "TEST_ONLY_DISPOSABLE_DB"
        or parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.path not in {"", "/"}
        or parsed.username
        or parsed.password
        or len(password) < 12
    ):
        print("E2E bloqueado: use HTTP localhost e autorize somente um banco descartável.", file=sys.stderr)
        return 2

    title = "E2E navegador " + uuid.uuid4().hex[:12]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(20000)

        try:
            page.goto(base, wait_until="domcontentloaded")
            page.get_by_label("E-mail").fill("ci-e2e@pulseops.invalid")
            page.locator("#login-password").fill(password)
            page.get_by_role("button", name="Entrar na plataforma").click()
            expect(page.get_by_role("heading", name=re.compile(r"^Visão geral")).first).to_be_visible()

            navigation = page.get_by_role("navigation", name="Navegação principal")
            navigation.get_by_role("button", name=re.compile("Equipes")).click()
            expect(page.get_by_role("heading", name="Equipes", exact=True).first).to_be_visible()

            navigation.get_by_role("button", name=re.compile("Usuários")).click()
            expect(page.get_by_role("heading", name="Administração de contas")).to_be_visible()
            account_form = page.locator(".operations-accounts .account-form")
            account_form.get_by_label("Nome completo").fill("Analista de Navegador")
            sample_email = "e2e-" + uuid.uuid4().hex[:12] + "@pulseops.invalid"
            account_form.get_by_label("E-mail").fill(sample_email)
            account_form.get_by_label("Senha inicial (mínimo 12 caracteres)").fill(password)
            account_form.get_by_role("button", name="Criar conta").click()
            account_row = page.locator('section[aria-label="Contas cadastradas"]').get_by_role("row").filter(has_text=sample_email)
            expect(account_row).to_be_visible()
            page.once("dialog", lambda dialog: dialog.accept())
            account_row.get_by_role("button", name="Desativar").click()
            expect(account_row.get_by_text("Inativa", exact=True)).to_be_visible()
            expect(page.get_by_role("heading", name="Últimas alterações de contas")).to_be_visible()

            navigation.get_by_role("button", name=re.compile("Central de IA")).click()
            expect(page.get_by_role("heading", name="Central de IA", exact=True).first).to_be_visible()
            expect(page.get_by_text("Demonstração — regras locais")).to_be_visible()

            navigation.get_by_role("button", name=re.compile("Chamados")).click()
            page.get_by_role("button", name=re.compile("Novo chamado")).click()
            create_dialog = page.get_by_role("dialog", name="Novo chamado")
            expect(create_dialog).to_be_visible()
            create_dialog.get_by_label("Título", exact=True).fill(title)
            create_dialog.get_by_label("Descrição").fill("Teste E2E fictício, sem dados reais.")
            create_dialog.get_by_role("button", name="Criar chamado").click()
            expect(create_dialog).not_to_be_visible()

            search = page.get_by_role("searchbox", name="Buscar chamados")
            search.fill(title)
            matching_row = page.get_by_role("row").filter(has_text=title)
            expect(matching_row).to_have_count(1)
            with page.expect_download() as download_info:
                page.get_by_role("button", name="Exportar CSV").click()
            download = download_info.value
            assert download.suggested_filename.endswith(".csv"), download.suggested_filename

            matching_row.get_by_role("button", name=re.compile("Abrir chamado")).click()
            details = page.get_by_role("dialog", name=title)
            expect(details).to_be_visible()
            assistant = details.get_by_role("region", name="Assistente de resolução")
            assistant.get_by_role("button", name="Gerar plano com IA").click()
            expect(assistant.get_by_text("Guia demonstrativo — não gerado por LLM")).to_be_visible()

            diagnostic_action = assistant.locator(".ticket-resolution-action").filter(
                has_text="Verificar saúde da plataforma"
            )
            approve_button = diagnostic_action.get_by_role("button", name="Revisar e executar")
            page.once("dialog", lambda dialog: dialog.dismiss())
            approve_button.click()
            expect(assistant.get_by_text("Diagnóstico do PulseOps AI concluído", exact=False)).to_have_count(0)

            page.once("dialog", lambda dialog: dialog.accept())
            approve_button.click()
            expect(assistant.get_by_text("Diagnóstico do PulseOps AI concluído", exact=False)).to_be_visible()
            expect(details.get_by_text("Aberto", exact=True).first).to_be_visible()

            details.get_by_role("button", name="Fechar detalhes").click()
            navigation.get_by_role("button", name="Minha conta").click()
            expect(page.get_by_role("heading", name="Minha conta", exact=True).first).to_be_visible()
            page.get_by_label("Senha atual").fill(password)
            new_password = "NovaSenha-" + password
            page.get_by_label("Nova senha", exact=True).fill(new_password)
            page.get_by_label("Confirme a nova senha").fill(new_password)
            page.get_by_role("button", name="Atualizar senha").click()
            expect(page.get_by_role("button", name="Entrar na plataforma")).to_be_visible()
            page.get_by_label("E-mail").fill("ci-e2e@pulseops.invalid")
            page.locator("#login-password").fill(new_password)
            page.get_by_role("button", name="Entrar na plataforma").click()
            expect(page.get_by_role("heading", name=re.compile(r"^Visão geral")).first).to_be_visible()
            page.get_by_role("button", name="Sair").click()
            expect(page.get_by_role("button", name="Entrar na plataforma")).to_be_visible()
            print("E2E aprovado: login, equipes, IA, ticket, CSV, plano, aprovação e logout.")
            return 0
        except Exception:
            page.screenshot(path="pulseops-e2e-failure.png", full_page=True)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
