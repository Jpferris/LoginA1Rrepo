# Versão 3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
import time
import csv

# CAMINHO DO PERFIL COM CERTIFICADO INSTALADO
user_data_dir = r"C:\Users\joao.ferri\AppData\Local\Google\Chrome\User Data" 
profile_dir = "Default"  # Troca se usar outro perfil

def iniciar_navegador():
    print("🚀 Iniciando navegador com certificado automático...")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--profile-directory={profile_dir}")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

def fechar_popup_automaticamente(driver):
    try:
        print("🧼 Tentando fechar popup de certificado expirando...")
        for i in range(5):
            try:
                botao_fechar = driver.find_element(By.XPATH,
                    "//span[@class='btn-fechar' and @onclick='fecharPopupAlertaCertificadoProximoDeExpirar()']")
                if botao_fechar.is_displayed():
                    ActionChains(driver).move_to_element(botao_fechar).click().perform()
                    print("✅ Popup fechado automaticamente!")
                    break
            except Exception as e:
                print(f"⚠️ Nenhum popup encontrado ainda... tentativa {i+1}/5.")
                time.sleep(2)
        else:
            print("🔁 Nenhum popup detectado ou erro ao localizar.")

        # Remover qualquer modal residual via JS
        driver.execute_script("""
            var modais = document.querySelectorAll('.rich-mpnl');
            modais.forEach(function(el) { el.remove(); });
        """)
    except Exception as e:
        print(f"❌ Erro ao tentar fechar o popup: {e}")

def extrair_cidades_pendentes(driver):
    try:
        print("🟢 Clicando no grupo 'Pendentes de ciência ou de resposta'")
        elemento_principal = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH,
                "//span[contains(text(), 'Pendentes de ciência ou de resposta')]/ancestor::a"))
        )
        elemento_principal.click()

        print("🟡 Aguardando carregamento completo da árvore...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".rich-tree-node-text.treeNodeItem"))
        )

        print("🔵 Coletando jurisdições e suas quantidades...")
        juris_nodes = driver.find_elements(By.CSS_SELECTOR, ".rich-tree-node-text.treeNodeItem")

        cidades_com_quantidade = []

        for node in juris_nodes:
            try:
                nome_cidade_elem = node.find_element(By.CSS_SELECTOR, "span.nomeTarefa")
                quantidade_elem = node.find_element(By.CSS_SELECTOR, "span.pull-right.mr-10")
                nome_cidade = nome_cidade_elem.text.strip()
                quantidade = quantidade_elem.text.strip()
                if nome_cidade and quantidade.isdigit():
                    cidades_com_quantidade.append({"cidade": nome_cidade, "pendencias": int(quantidade)})
            except Exception:
                continue  # Ignorar nós que não têm ambos os elementos esperados

        print(f"✅ {len(cidades_com_quantidade)} cidades encontradas com pendências.")
        return cidades_com_quantidade

    except Exception as e:
        print(f"❌ Erro ao extrair cidades: {e}")
        return []

def extrair_processos_da_jurisdicao(driver, cidade_nome):
    """Função que entra na jurisdição e extrai os processos"""
    try:
        print(f"🔍 Abrindo jurisdição: {cidade_nome}")
        elemento = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[@class='nomeTarefa' and contains(text(), '{cidade_nome}')]"))
        )
        elemento.click()

        print("⏳ Aguardando carregamento dos processos...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".rich-table-cell .numero-processo-expediente"))
        )

        linhas_tabela = driver.find_elements(By.CSS_SELECTOR, "tr.rich-table-row")

        processos = []
        for linha in linhas_tabela:
            try:
                numero_link = linha.find_element(By.CSS_SELECTOR, "a.numero-processo-expediente")
                tipo_documento = linha.find_element(By.CSS_SELECTOR, "span[title='Tipo de documento']").text.strip()
                data_publicacao = linha.find_element(By.CSS_SELECTOR, "span[title='Data de criação do expediente']").text.strip()
                prazo_manifestacao = linha.find_element(By.CSS_SELECTOR, "div[title='Prazo para manifestção']").text.strip()
                link = numero_link.get_attribute("onclick").split("'")[1].replace("/pje/Processo/ConsultaProcesso/Detalhe/", "")

                # Extrair número do processo
                numero_processo = numero_link.text.strip()
                link_completo = f"https://pje.tjes.jus.br/pje/Processo/ConsultaProcesso/Detalhe/ {link}"

                processos.append({
                    "numero_processo": numero_processo,
                    "tipo_documento": tipo_documento,
                    "data_publicacao": data_publicacao,
                    "prazo_manifestacao": prazo_manifestacao,
                    "link": link_completo
                })
            except Exception as e:
                print(f"⚠️ Erro ao extrair linha: {e}")
                continue

        print(f"✅ {len(processos)} processos extraídos de {cidade_nome}")
        return processos

    except Exception as e:
        print(f"❌ Erro ao extrair processos de {cidade_nome}: {e}")
        return []

def salvar_em_csv(dados, caminho_arquivo="processos_pendentes.csv"):
    with open(caminho_arquivo, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["numero_processo", "tipo_documento", "data_publicacao", "prazo_manifestacao", "link"])
        writer.writeheader()
        writer.writerows(dados)
    print(f"💾 Dados salvos em {caminho_arquivo}")

def main():
    driver = iniciar_navegador()
    driver.get("https://pje.tjes.jus.br/pje/Painel/painel_usuario/advogado.seam ")

    print("⏳ Aguardando login manual com certificado digital...")

    try:
        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("✅ Login detectado. Página carregada.")

        fechar_popup_automaticamente(driver)

        dados_cidades = extrair_cidades_pendentes(driver)

        todos_os_processos = []

        for cidade in dados_cidades:
            processos = extrair_processos_da_jurisdicao(driver, cidade["cidade"])
            todos_os_processos.extend(processos)

        print("\n📊 RESUMO DOS PROCESSOS ENCONTRADOS:")
        for p in todos_os_processos:
            print(f"{p['numero_processo']} | {p['tipo_documento']} | Publicado em: {p['data_publicacao']} | Prazo: {p['prazo_manifestacao']}")

        # Descomente para salvar em CSV
        # salvar_em_csv(todos_os_processos)

    except Exception as e:
        print(f"💥 Erro durante execução: {e}")
    finally:
        print("🚪 Fechando o navegador automaticamente...")
        driver.quit()

if __name__ == "__main__":
    main()