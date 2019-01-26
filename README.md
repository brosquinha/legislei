![build](https://img.shields.io/travis/com/brosquinha/politica.svg)
![Python 3.5+](https://img.shields.io/badge/python-3.5^-blue.svg)
![glp](https://img.shields.io/github/license/brosquinha/politica.svg)
# Legislei

Projeto de constante monitoramento das atividades de parlamentares de todas as três esferas federativas. As casas legislativas cadastradas até o momento são:

* [Câmara Municipal de São Paulo](http://www.saopaulo.sp.leg.br/transparencia/dados-abertos/dados-disponibilizados-em-formato-aberto/)
* [ALESP](https://www.al.sp.gov.br/dados-abertos/)
* [Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html)

## Clonar repositório git

Para obter o código-fonte da aplicação Legislei, clone o repositório git com o seguinte comando:

```Bash
git clone https://github.com/brosquinha/politica.git
```

## Definir as variaveis de ambiente em \.env

A seguir, acesse a pasta raíz do projeto e crie o arquivo `.env` dentro da pasta `legislei` com as seguintes variáveis de ambiente:

| Nome da variável | Descrição |
| ---------------- | --------- |
| APP_SECRET_KEY | Chave secreta para a aplicação Flask |
| HOST_ENDPOINT | Endpoint do host |
| DEBUG | `True` para roda a aplicação no modo de debug do Flask |
| EMAIL_ENDPOINT | Endpoint para o server SMTP |
| EMAIL_PORT | Porta para o server SMTP |
| EMAIL_SSL | `True` se o server SMTP trabalha com SSL |
| EMAIL_TLS | `True` se o server SMTP trabalha com TLS |
| EMAIL_USR | Endereço de email do gmail para envio de relatórios |
| EMAIL_PSW | Senha do email do gmail para envio de relatórios |
| PORT | Porta para expor a aplicação Flask |
| MONGODB_URI | URI de conexão para o MongoDB (normalmente utilizado em produção) |
| MONGODB_HOST | Host de conexão para o MongoDB (normalmente utilizado em desenvolvimento) |
| MONGODB_PORT | Porta da conexão para o MongoDB (normalmente utilizado em desenvolvimento) |
| MONGODB_DBNAME | Nome do banco de dados da aplicação no MongoDB |

## Instalar pacotes Python 3.5+ e virtualenv

Para instalar o pacote `virtualenv`:

```Bash
pip install virtualenv
```

Criar o ambiente virtual para a aplicação Legislei, rode o seguinte na pasta raíz do projeto:

```Bash
virtualenv politica
source politica/bin/activate
```

Para instalar as dependências do projeto, rode:

```Bash
pip install -r requirements.txt
```

Por fim, crie o arquivo `.env` na pasta `legislei` do projeto com as variáveis de ambiente necessárias e rode:

```Bash
python app.py
```

Para desativar o ambiente virtual atual:

```Bash
deactivate
```

## Testando

Para rodar os testes de unidade:

```Bash
python -m unittest discover -s tests/unit
```

Para rodar os testes de integração, certifique-se de que você configurou as [variávies de ambiente](#definir-as-variaveis-de-ambiente-em-env) relacionadas ao banco de dado MongoDB e que sua conexão com a internet está funcionando, porque esses testes fazem uso desses recursos. Uma vez que tudo isso esteja funcionando, rode:

```Bash
python -m unittest discover -s tests/integration
```

Note que esses testes podem demorar até 6 minutos, dependendo de sua conexão com a internet e da velocidade de conexão ao banco de dados.

Para gerar o relatório de cobertura de testes:

```Bash
coverage run run_tests.py
coverage html
```

## Docker

Para construir a imagem:

```Bash
cd Politica
docker build -t legislei .
```

Para rodar o container:

```Bash
docker run -p 8080:8080 --env-file legislei/.env legislei
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
