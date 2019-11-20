[![Build Status](https://travis-ci.com/brosquinha/legislei.svg?branch=master)](https://travis-ci.com/brosquinha/legislei)
![Python 3.5+](https://img.shields.io/badge/python-3.5^-blue.svg)
![glp](https://img.shields.io/github/license/brosquinha/legislei.svg)
[![codecov](https://codecov.io/gh/brosquinha/legislei/branch/master/graph/badge.svg)](https://codecov.io/gh/brosquinha/legislei)
[![Documentation Status](https://readthedocs.org/projects/legislei/badge/?version=latest)](https://legislei.readthedocs.io/pt/latest/?badge=latest)
# Legislei

Projeto de constante monitoramento das atividades de parlamentares de todas as três esferas federativas. As casas legislativas cadastradas até o momento são:

* [Câmara Municipal de São Paulo](http://www.saopaulo.sp.leg.br/transparencia/dados-abertos/dados-disponibilizados-em-formato-aberto/)
* [ALESP](https://www.al.sp.gov.br/dados-abertos/)
* [Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html)

## Setup

### Clonar repositório git

Para obter o código-fonte da aplicação Legislei, clone o repositório git com o seguinte comando:

```Bash
git clone https://github.com/brosquinha/legislei.git
```

### Definir as variaveis de ambiente em \.env

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
| FIREBASE_API_TOKEN | Token da API REST legada do Firebase para envio de Push Notifications |
| PORT | Porta para expor a aplicação Flask |
| MONGODB_URI | URI de conexão para o MongoDB (normalmente utilizado em produção) |
| MONGODB_HOST | Host de conexão para o MongoDB (normalmente utilizado em desenvolvimento) |
| MONGODB_PORT | Porta da conexão para o MongoDB (normalmente utilizado em desenvolvimento) |
| MONGODB_DBNAME | Nome do banco de dados da aplicação no MongoDB |
| SENTRY_DSN | DSN do Sentry |

### Instalar pacotes Python 3.5+ e virtualenv

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

### Testando

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

### Gerar HTML de documentação

Rodar o seguinte na pasta raíz:

```Bash
cd docs/
make html
```

### Rodando as migrations

Para rodar as migrations de banco de dados, vá para a pasta raíz do projeto e crie a pasta `.migrations`. Nela, crie o arquivo `config.json` com o seguinte conteúdo:

```json
{
    "migrations_db_name": "MONGODB_DATABASE",
    "migrations_coll_name": "migrations",
    "mongo_uri": "MONGODB_URI"
}
```

Substitua `MONGODB_DATABASE` e `MONGODB_URI` pelo seus respectivo valores. Depois, crie hardlinks apontando para as migrations que quer rodar (usando o mesmo nome do arquivo apontado) e rode o seguinte:

```Bash
cd ..
docker run -e env=dev -v $(pwd)/.migrations/config.json:/app/src/config/config.dev.json -v $(pwd)/.migrations:/app/src/migrations skynyrd/cikilop
```

Para reverter as migrations:

```Bash
cd ..
docker run -e env=dev -v $(pwd)/.migrations/config.json:/app/src/config/config.dev.json -v $(pwd)/.migrations:/app/src/migrations skynyrd/cikilop --revert
```

## Executando no Docker

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

## Contribuindo

### Acrescentar uma nova casa legislativa

Para acrescentar uma nova casa legislativa ao projeto, primeiro é necessário entender a lógica do sistema Legislei.

O sistema Legislei é formado por camadas, cada uma com uma responsabilidade bem determinada. A camada web é responsável
pelo tratamento de requisições HTTP. Cabe a essa camada, por exemplo, apresentar os relatórios gerados pela próxima camada do sistema:
os house handlers. Cada casa legislativa tem seu handler próprio, que é responsável por gerar os relatórios de parlamentares e dados dos
seus parlamentares. Essa camada faz uso intensivo da última camada, as bibliotecas (libs) das casas legislativas. Essas libs são basicamente wrappers das
API de cada casa, e são responsáveis por recuperar e apresentar os dados disponíveis pelas APIs de Dados Abertos das casas legislativas.
Eventualmente, essas libs devem ser publicadas no repositório PyPi para serem utilizadas por qualquer outro projeto que precise de seus dados.

Portanto, para se acrescentar uma nova casa legislativa ao sistema, é necessário desenvolver o house handler e a biblioteca de dados da casa,
se já não houver alguma disponível.

#### House hanlder

O house handler deve ter conhecimento de como estruturar os dados fornecidos pela biblioteca da casa para disponibilizar para as
camadas superiores os seguintes dados:

* Relatório de atividades de um dado parlamentar em um dado intervalo de tempo;
* Informações de um dado parlamentar;
* Lista de parlamentares atuais com informações básicas.

Um relatório de atividades deve conter os seguintes dados:

* Dados do parlamentar do período;
* Comissões das quais o parlamentar faz parte, e qual cargo ele possuí (Titular ou Suplente);
* Proposições do parlamentar no período, se houver;
* Eventos que o parlamentar esteve presente, se houver, com informações de pautas e votações;
* Eventos que o parlamentar estava previsto, mas ausentou-se, se houver;
* Eventos que o parlamentar ausentou-se, se houver;

Toda house handler é um classe filha de `CasaLegislativa`, e deve implementar os seguintes métodos:

* `obter_relatorio(parlamentar_id : String, data_final : datetime, periodo_dias : Integer) : Relatorio`
* `obter_parlamentar(parlamentar_id : String) : Parlamentar`
* `obter_arpamentares() : List of dict`

Consulte a [documentação](http://legislei.readthedocs.io/) para mais detalhes sobre as classes `CasaLegislativa`, `Relatorio` e `Parlamentar`.

Uma vez implementada o handler, atualize o dicionário `house_selector_dict` do arquivo `house_selector.py` com
o identificador da sua casa, seguindo a seguinte regra:

* `BR1` é Câmara dos Deputados e `BR2` é Senado Federal;
* A sigla da UF para as assembleias legislativas estaduais (e.g., `SP`, `BA`, etc);
* Nome do munincípio em maiúsculas para câmaras municipais (e.g., `SÃO PAULO`, `SALVADOR`).

### Biblioteca de API

Se não existir uma biblioteca de abstração da API da casa legislativa, você terá que criá-la também. É importante
que essa biblioteca seja independente do projeto Legislei, para que possa ser eventualmente publicada à parte no
repositório do PyPi para todos possam usá-la em outros projetos. Dessa forma, essa biblioteca não deve se preocupar
em formatar seus dados pensando no handler; ao contrário, deve fornecê-los da maneira que faça mais sentido tendo em
mente a API da casa legislativa. É função do house handler organizar os esses dados para entregar os relatórios.

## Outras contribuições

Toda e qualquer ajuda ao projeto é bem-vinda. Caso queira contribuir com outro aspecto do sistema, você pode abrir
uma issue no GitHub para discussão de algum ponto e/ou criar um fork para depois abrir um Pull Request com sugestão
de alterações.
