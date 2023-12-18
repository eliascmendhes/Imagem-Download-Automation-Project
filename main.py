from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from urllib.parse import urlencode
import os
import time
from datetime import datetime

# URL da página que contém os links das imagens
url = "https://www.shesfixingherhair.co.uk/gallery/index.php"

# Termo de pesquisa para identificar os links das imagens
termo_pesquisa = "displayimage.php?pid="

# Diretórios para imagens e logs
diretorio_imagens = os.path.join(os.getcwd(), "images")
diretorio_log = os.path.join(os.getcwd(), "log")

# Verifica se os diretórios existem, se não, cria-os
for diretorio in [diretorio_imagens, diretorio_log]:
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)

# Instância do driver do Chrome
driver = webdriver.Chrome()

# Caminho para o arquivo de log de imagens existentes
arquivo_log_imagens_exist = os.path.join(diretorio_log, "log_imagens_exist.txt")

# Dicionário para rastrear a contagem de imagens já existentes
contagem_imagens_exist = {}

# Número desejado de imagens a serem baixadas antes de recarregar a página
num_imagens_por_recarga = 10
imagens_baixadas = 0
tentativas_baixar = 0
limite_tentativas_sem_recarga = 5  # Número máximo de tentativas sem recarregar a página

try:
    # Informações para o log inicial
    numero_sessao = datetime.now().strftime("%Y%m%d%H%M%S")
    hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Abre o arquivo de log inicial ou cria um novo se não existir
    with open(os.path.join(diretorio_log, f"internetthings_{numero_sessao}.txt"), "w") as log_inicial:
        log_inicial.write(f"Número da Sessão: {numero_sessao}\n")
        log_inicial.write(f"Hora de Início: {hora_inicio}\n")

    # Abre o navegador e acessa a URL
    driver.get(url)

    # Aguarda o carregamento da página
    time.sleep(2)

    # Lista para armazenar todos os links de imagens encontrados
    links_imagens = []

    # Enquanto houver mais links de imagens na página
    while True:
        # Encontra todos os links de imagens na página
        links_imagens = driver.find_elements(By.XPATH, f".//a[contains(@href, '{termo_pesquisa}')]")

        # Rola a página para baixo para carregar mais imagens
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Aguarda um curto período para o carregamento das imagens
        time.sleep(2)

        # Se não houver mais links, encerra o loop
        if not links_imagens:
            break

        # Itera sobre todos os links de imagens encontrados
        for link_imagem in links_imagens:
            try:
                # Extrai o ID da imagem a partir do link
                id_imagem = link_imagem.get_attribute("href").split("?")[1].split("=")[1]

                # Constrói a URL da imagem em tamanho completo sem #top_display_media
                base_url = "https://www.shesfixingherhair.co.uk/gallery/displayimage.php"
                parametros = {"pid": id_imagem, "fullsize": 1}
                url_tamanho_completo = f"{base_url}?{urlencode(parametros)}"

                # Exibe a URL da imagem em tamanho completo
                print("URL da imagem em tamanho completo:", url_tamanho_completo)

                # Acessa a URL da imagem em tamanho completo
                driver.get(url_tamanho_completo)

                # Aguarda o carregamento da imagem em tamanho completo
                time.sleep(2)

                # Encontra o elemento que contém a imagem em tamanho completo
                elemento_imagem_tamanho_completo = driver.find_element(By.XPATH, "//img[contains(@src, 'albums')]")

                # Extrai a URL da imagem em tamanho completo
                url_imagem_tamanho_completo = elemento_imagem_tamanho_completo.get_attribute("src")

                # Extrai o atributo alt da tag img
                atributo_alt = elemento_imagem_tamanho_completo.get_attribute("alt")

                # Usa o alt como o nome do arquivo (remove caracteres inválidos)
                nome_arquivo = f"{atributo_alt}.jpg".replace("/", "_").replace("\\", "_")

                # Incrementa o contador de tentativas de baixar
                tentativas_baixar += 1

                # Verifica se o arquivo já existe
                if os.path.exists(os.path.join(diretorio_imagens, nome_arquivo)):
                    # Escreve a contagem no arquivo de log
                    with open(arquivo_log_imagens_exist, "a") as log_file:
                        log_file.write(f"{nome_arquivo},{tentativas_baixar}\n")

                    print(f"Imagem {id_imagem} já existente. Tentativa: {tentativas_baixar}")

                else:
                    # Baixa a imagem usando o requests
                    resposta = requests.get(url_imagem_tamanho_completo)
                    with open(os.path.join(diretorio_imagens, nome_arquivo), "wb") as f:
                        f.write(resposta.content)

                    print(f"Imagem {id_imagem} salva como {nome_arquivo}.")

                    # Escreve a informação no log inicial
                    with open(os.path.join(diretorio_log, f"internetthings_{numero_sessao}.txt"), "a") as log_inicial:
                        log_inicial.write(f"Imagem {id_imagem} salva como {nome_arquivo}.\n")

                    imagens_baixadas += 1

                    # Se atingir o número desejado de imagens baixadas, recarrega a página
                    if imagens_baixadas >= num_imagens_por_recarga:
                        imagens_baixadas = 0  # Reinicia a contagem
                        tentativas_baixar = 0  # Reinicia a contagem de tentativas
                        driver.get(url)  # Recarrega a página inicial

            except Exception as e:
                # Tratamento de erro
                print("Erro ao processar a imagem:", str(e))

            # Retorna à página inicial para a próxima iteração
            driver.back()

            # Aguarda um curto período para evitar problemas na transição de páginas
            time.sleep(1)

        # Se atingir o limite de tentativas sem recarregar, recarrega a página
        if tentativas_baixar >= limite_tentativas_sem_recarga:
            tentativas_baixar = 0  # Reinicia a contagem
            driver.get(url)  # Recarrega a página inicial

    # Informações para o log final
    hora_fim = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Abre o arquivo de log inicial e adiciona as informações finais
    with open(os.path.join(diretorio_log, f"internetthings_{numero_sessao}.txt"), "a") as log_inicial:
        log_inicial.write(f"Hora de Término: {hora_fim}\n")
        log_inicial.write(f"Total de Links de Imagens Encontrados: {len(links_imagens)}\n")
        log_inicial.write(f"Total de Imagens Salvas: {len(contagem_imagens_exist)}\n")

except KeyboardInterrupt:
    print("Programa interrompido manualmente.")

finally:
    # Fecha o navegador
    driver.quit()
