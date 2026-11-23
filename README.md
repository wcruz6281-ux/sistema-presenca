# Sistema de Controle de Presenca Escolar

Sistema web para cadastro de turmas e alunos, registro manual de presenca e utilizacao de reconhecimento facial com OpenCV. O projeto foi desenvolvido com base na especificacao localizada em `docs/presenca_escolar_reconhecimento_facial (3).docx`.

## Contexto do projeto

Projeto desenvolvido em aula no Curso Técnico em Desenvolvimento de Sistemas, com orientação do professor [Eduardo Hernandes](https://github.com/eduhernandes).

## Funcionalidades

- Cadastro e consulta de turmas.
- Cadastro e consulta de alunos.
- Vinculo de alunos a turmas.
- Registro de presenca manual pela interface web.
- Impedimento de presenca duplicada no mesmo dia.
- Dashboard com indicadores e registros recentes.
- Cadastro facial pela webcam no navegador ou por script local.
- Treinamento de modelo LBPH para reconhecimento facial.
- Reconhecimento pela webcam e registro automatico da presenca.
- Exclusao das imagens faciais cadastradas para um aluno.

## Tecnologias

- Python
- FastAPI
- SQLAlchemy
- SQLite
- OpenCV e `cv2.face`
- HTML, CSS e JavaScript
- Uvicorn

## Estrutura do projeto

```text
sistema-presenca/
|-- main.py                 # Aplicacao FastAPI e rotas administrativas
|-- database.py             # Configuracao da conexao SQLite
|-- models.py               # Modelos de Turma, Aluno e Presenca
|-- rosto_api.py            # Endpoints para cadastro e treinamento facial
|-- cadastrar_rosto.py      # Captura facial pelo terminal
|-- treinar_rosto.py        # Treinamento do modelo facial pelo terminal
|-- reconhecer_rosto.py     # Reconhecimento pela webcam e registro de presenca
|-- detectar_rosto.py       # Teste de deteccao facial
|-- teste_camera.py         # Teste da webcam
|-- static/                 # Interface web
|-- docs/                   # Especificacao de requisitos
|-- rostos_alunos/          # Imagens faciais por aluno
|-- modelo_rosto.yml        # Modelo LBPH treinado
|-- presenca.db             # Banco SQLite
`-- README.md
```

## Requisitos

- Windows
- Python 3.10 ou superior
- Webcam
- Navegador com acesso a webcam
- Permissao para executar scripts e instalar pacotes

## Instalacao

No terminal, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy opencv-contrib-python numpy
```

Se a ativacao do ambiente virtual estiver bloqueada pelo PowerShell, execute apenas uma vez:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Execucao

Inicie o servidor:

```powershell
uvicorn main:app --reload
```

Acesse:

- Interface: http://127.0.0.1:8000
- Documentacao Swagger: http://127.0.0.1:8000/docs

O banco `presenca.db` e as tabelas sao criados automaticamente na primeira execucao.

## Fluxo de uso

1. Cadastre uma turma.
2. Cadastre os alunos e vincule-os a uma turma.
3. Abra a secao **Cadastro facial**.
4. Selecione o aluno e confirme a autorizacao adequada.
5. Ligue a camera e capture cerca de 20 imagens com pequenas variacoes de posicao.
6. Cadastre todos os alunos desejados.
7. Clique em **Treinar modelo** ou execute `python treinar_rosto.py`.
8. Execute `python reconhecer_rosto.py` para iniciar o reconhecimento.
9. Pressione `Q` na janela da webcam para encerrar.

O cadastro facial tambem pode ser realizado pelo terminal:

```powershell
python cadastrar_rosto.py
python treinar_rosto.py
python reconhecer_rosto.py
```

## Testes da webcam e deteccao

Testar se a webcam abre:

```powershell
python teste_camera.py
```

Testar somente a deteccao de rostos:

```powershell
python detectar_rosto.py
```

## Reconhecimento facial

As imagens sao armazenadas em `rostos_alunos/aluno_<ID>/` e o modelo treinado em `modelo_rosto.yml`.

O reconhecimento usa o algoritmo LBPH do OpenCV. O classificador foi configurado para registrar uma presenca apenas para alunos ativos, respeitando a distancia inicial de reconhecimento definida no codigo e evitando tentativas repetidas dentro do intervalo configurado.

O reconhecimento facial pode produzir erros. O sistema atual deve ser usado em ambiente piloto e possui um metodo manual de presenca pela interface web como alternativa.

## Endpoints principais

| Metodo | Endpoint | Finalidade |
|---|---|---|
| `POST` | `/turmas` | Cadastrar turma |
| `GET` | `/turmas` | Listar turmas |
| `POST` | `/alunos` | Cadastrar aluno |
| `GET` | `/alunos` | Listar alunos |
| `POST` | `/presencas/registrar` | Registrar presenca |
| `GET` | `/dashboard/resumo` | Consultar resumo do dashboard |
| `GET` | `/rostos/status` | Consultar quantidade de imagens |
| `POST` | `/alunos/{aluno_id}/rosto/imagem` | Salvar imagem facial |
| `POST` | `/rostos/treinar` | Treinar o modelo facial |
| `DELETE` | `/alunos/{aluno_id}/rosto` | Excluir imagens faciais |

Consulte todos os parametros e respostas em http://127.0.0.1:8000/docs.

## Importante sobre privacidade

Antes de cadastrar dados biometricos de menores:

- Obtenha orientacao juridica e da equipe de protecao de dados da instituicao.
- Documente a finalidade, a base legal e as exigencias aplicaveis da LGPD.
- Informe estudantes e responsaveis sobre coleta, uso, acesso, armazenamento e exclusao.
- Restrinja o acesso a imagens, modelos e registros.
- Defina prazos de retencao e procedimentos de exclusao.
- Mantenha uma forma alternativa de registrar a presenca.
- Permita revisao humana das identificacoes inconclusivas.
- Realize testes de precisao, falsos positivos, falsos negativos e tratamento de baixa qualidade em ambiente controlado.

O reconhecimento facial isoladamente nao deve ser considerado prova infalivel de presenca. Qualquer identificacao inconclusiva deve ser conferida por profissional autorizado.

## Dados gerados

Os seguintes arquivos e pastas podem conter dados pessoais ou biometricos:

- `presenca.db`
- `rostos_alunos/`
- `modelo_rosto.yml`
- `presenca_backup.db`, quando criada uma copia manual

Esses dados nao devem ser enviados a repositorios publicos. O `.gitignore` do projeto ja exclui bancos, modelo facial e imagens faciais.

## Consideracoes de implantacao

Esta versao utiliza SQLite e um processo local do FastAPI. Para uso em varias unidades ou varias cameras, a especificacao sugere avaliar PostgreSQL, autenticacao, TLS, monitoramento, backups, controle de permissoes e implantar em infraestrutura privada antes de colocar o sistema em producao.
