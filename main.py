import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# --- Configurações Globais ---
USER_DATA_DIR = r"C:\Users\joao.ferri\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR = "Default"
PJE_URL = "https://pje.tjes.jus.br/pje/Painel/painel_usuario/advogado.seam"

# --- IMPORTANTE: Caminho para o driver manual ---
# Coloque o caminho completo para o chromedriver.exe que você baixou.
# O 'r' antes da string é importante para lidar com as barras invertidas do Windows.
# DICA: Crie uma pasta 'drivers' dentro do seu projeto e coloque o .exe lá.
CAMINHO_DRIVER = r"C:\Users\joao.ferri\Desktop\PJ_ES_AUTOMAÇÃO\drivers\chromedriver.exe"

def iniciar_navegador():
    """
    Inicia o Chrome usando um chromedriver.exe local (modo offline).
    """
    print("🚀 Iniciando navegador com driver manual (modo offline)...")
    
    # Validação para garantir que o arquivo do driver existe antes de continuar
    if not os.path.exists(CAMINHO_DRIVER):
        print(f"💥 ERRO: O arquivo do ChromeDriver não foi encontrado em: {CAMINHO_DRIVER}")
        print("💥 Por favor, baixe o driver correto e atualize a variável 'CAMINHO_DRIVER' no código.")
        return None # Retorna None para indicar falha

    options = Options()
    options.add_argument("--start-maximized")
    #options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    #options.add_argument(f"--profile-directory={PROFILE_DIR}")

    # Argumentos de estabilidade para previnir crashes na inicialização
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    service = Service(executable_path=CAMINHO_DRIVER)
    
    return webdriver.Chrome(service=service, options=options)

# ... (As outras funções 'fechar_popup_automaticamente' e 'extrair_cidades_pendentes' permanecem as mesmas) ...
def fechar_popup_automaticamente(driver):
    """Tenta fechar o popup de alerta do certificado de forma robusta."""
    print("🧼 Tentando fechar o popup de certificado...")
    try:
        wait = WebDriverWait(driver, 10)
        botao_fechar = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[@class='btn-fechar' and @onclick='fecharPopupAlertaCertificadoProximoDeExpirar()']"))
        )
        botao_fechar.click()
        print("✅ Popup fechado com sucesso via clique.")
    except Exception:
        print("⚡ Popup não encontrado ou não clicável. Tentando remover com JavaScript como fallback...")
        try:
            driver.execute_script("""
                var popup = document.getElementById('popupAlertaCertificadoProximoDeExpirar');
                if (popup) { popup.remove(); }
                var modais = document.querySelectorAll('.rich-mpnl');
                modais.forEach(function(el) { el.remove(); });
            """)
            print("🧨 Popup removido via JavaScript!")
        except Exception as js_e:
            print(f"💥 Falha ao tentar remover o popup com JavaScript: {js_e}")

def extrair_cidades_pendentes(driver):
    """Clica em 'Pendentes' e extrai a lista de cidades."""
    try:
        print("🟢 Clicando no menu de pendências...")
        wait = WebDriverWait(driver, 15)
        pendente_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Pendentes de ciência ou de resposta')]"))
        )
        pendente_btn.click()

        print("🟡 Esperando a árvore de cidades carregar...")
        wait.until(
            EC.presence_of_element_located((By.ID, "formAbaExpediente:listaAgrSitExp:0:trPend"))
        )

        print("🔵 Extraindo os nomes das cidades...")
        spans = driver.find_elements(By.CSS_SELECTOR, "span.nomeTarefa")
        
        cidades = [
            span.text.strip() for span in spans 
            if span.text.strip() and "Pendentes de ciência" not in span.text
        ]

        print(f"✅ {len(cidades)} cidades encontradas.")
        return cidades
    except Exception as e:
        print(f"❌ Erro no scraping: {e}")
        return []


def main():
    """Função principal para orquestrar a automação."""
    driver = None
    try:
        driver = iniciar_navegador()
        if driver is None:
            # Se a inicialização falhou (driver não encontrado), encerra o script.
            return

        driver.get(PJE_URL)
        print("⏳ Aguardando login manual com certificado...")

        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.ID, "formAbaExpediente"))
        )
        print("✅ Login detectado. Página carregada.")

        fechar_popup_automaticamente(driver)
        cidades = extrair_cidades_pendentes(driver)

        print("\n📊 CIDADES COM PENDÊNCIA DE CIÊNCIA:")
        for cidade in cidades:
            print(f"📍 {cidade}")

    except Exception as e:
        print(f"💥 Ocorreu um erro fatal na execução principal: {e}")
    finally:
        if driver:
            print("🚪 Fechando o navegador automaticamente...")
            driver.quit()

if __name__ == "__main__":
    main()