# Legislei

Projeto pessoal de constante monitoramento das atividades de políticas na Câmara Municipal de São Paulo, Assembleia Legislativa de SP e Câmara dos Deputados.

Links de refência:

* [Câmara Municipal de São Paulo](http://www.saopaulo.sp.leg.br/transparencia/dados-abertos/dados-disponibilizados-em-formato-aberto/)
* [ALESP](https://www.al.sp.gov.br/dados-abertos/)
* [Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html)

**ATENÇÃO**: as instruções a seguir ainda são referentes ao meu setup pessoal (RPi3). Antes de publicar, fazer as alterações adequadas (como trocar `python3` e `pip3` para `python` e `pip` e trocar a URL do repositório git).

## Clonar repositório git

Para obter o código-fonte da aplicação Legislei, clone o repositório git com o seguinte comando:

```Bash
git clone pi@192.168.1.72:/home/pi/Projects/Politica
```

## Definir as variáveis de ambiente em \.env

A seguir, acesse a pasta raíz do projeto e crie o arquivo `.env` com as seguintes variáveis de ambiente:

| Nome da variável | Descrição |
| ---------------- | --------- |
| DEBUG | `True` para roda a aplicação no modo de debug do Flask |
| GMAIL_USR | Endereço de email do gmail para envio de relatórios |
| GMAIL_PSW | Senha do email do gmail para envio de relatórios |
| PORT | Porta para expor a aplicação Flask |
| MONGODB_URI | URI de conexão para o MongoDB (normalmente utilizado em produção) |
| MONGODB_HOST | Host de conexão para o MongoDB (normalmente utilizado em desenvolvimento) |
| MONGODB_PORT | Porta da conexão para o MongoDB (normalmente utilizado em desenvolvimento) |
| MONGODB_DBNAME | Nome do banco de dados da aplicação no MongoDB |

## Instalar pacotes Python e virtualenv

Para instalar o pacote `virtualenv`:

```Bash
pip3 install virtualenv
```

Criar o ambiente virtual para a aplicação Legislei, rode o seguinte na pasta raíz do projeto:

```Bash
virtualenv politica
source politica/bin/activate
```

Por fim, crie o arquivo `.env` na pasta raíz do projeto com as variáveis de ambiente necessárias e rode:

```Bash
python3 app.py
```

Para desativar o ambiente virtual atual:

```Bash
deactivate
```

## Docker

Para construir a imagem:

```Bash
cd Politica
docker build -t legislei .
```

Para rodar o container:

```Bash
docker run -p 8080:8080 --env-file .env legislei
```

Para rodar o compose Docker:

```Bash
docker-compose up
```

## Gerar HTML de documentação

Rodar o seguinte na pasta raíz:

```Bash
sphinx-apidoc -o docs/_modules .
cd docs/
make html
```
