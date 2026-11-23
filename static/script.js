// ---------- Mensagens ----------
// Mostra feedback colorido: tipo = "sucesso" ou "erro".
function mostrarMensagem(elemento, texto, tipo) {
    elemento.textContent = texto;
    elemento.className = "mensagem " + tipo;
}

// ---------- Navegação ----------
// Troca a seção visível e mantém o item do menu lateral em sincronia,
// inclusive quando a navegação vem dos botões de "Acesso rápido".
function mostrarSecao(id) {
    document.querySelectorAll(".painel").forEach((painel) => {
        painel.hidden = true;
    });

    document.getElementById(id).hidden = false;

    document.querySelectorAll(".menu-item[onclick]").forEach((item) => {
        const destino = item.getAttribute("onclick").includes(`'${id}'`);
        item.classList.toggle("ativo", destino);
    });

    if (id === "secao-inicio") {
        carregarResumo();
    }

    if (id === "secao-alunos") {
        carregarTurmas();
        listarAlunos();
    }

    if (id === "secao-turmas") {
        listarTurmas();
    }
}

// ---------- Visão geral (dados reais do dashboard) ----------
function definirTexto(id, texto) {
    const elemento = document.getElementById(id);

    if (elemento) {
        elemento.textContent = texto;
    }
}

function formatarData(iso) {
    const [ano, mes, dia] = iso.split("-");
    return `${dia}/${mes}/${ano}`;
}

async function carregarResumo() {
    const recentes = document.getElementById("lista-recentes");

    try {
        const resposta = await fetch("/dashboard/resumo");

        if (!resposta.ok) {
            throw new Error("Falha ao buscar o resumo.");
        }

        const dados = await resposta.json();

        definirTexto("resumo-ativos", dados.alunos_ativos);
        definirTexto(
            "resumo-total",
            `de ${dados.total_alunos} cadastrados`
        );
        definirTexto("resumo-turmas", dados.total_turmas);
        definirTexto("resumo-presencas", dados.presencas_hoje);
        definirTexto("resumo-sem-registro", dados.sem_registro_hoje);

        recentes.replaceChildren();

        if (dados.registros_recentes.length === 0) {
            recentes.textContent = "Nenhum registro de presença ainda.";
            return;
        }

        const tabela = document.createElement("table");
        tabela.className = "tabela-alunos";

        const cabecalho = document.createElement("thead");
        const linhaCabecalho = document.createElement("tr");

        ["Aluno", "Matrícula", "Data", "Hora", "Status"].forEach((titulo) => {
            const th = document.createElement("th");
            th.textContent = titulo;
            th.scope = "col";
            linhaCabecalho.appendChild(th);
        });

        cabecalho.appendChild(linhaCabecalho);
        tabela.appendChild(cabecalho);

        const corpo = document.createElement("tbody");

        dados.registros_recentes.forEach((registro) => {
            const linha = document.createElement("tr");

            [
                registro.aluno,
                registro.matricula,
                formatarData(registro.data),
                registro.hora,
                registro.status
            ].forEach((valor) => {
                const celula = document.createElement("td");
                celula.textContent = valor;
                linha.appendChild(celula);
            });

            corpo.appendChild(linha);
        });

        tabela.appendChild(corpo);
        recentes.appendChild(tabela);
    } catch (erro) {
        recentes.textContent = "Erro ao carregar o resumo: " + erro.message;
    }
}

// ---------- Alunos ----------
// Carregar turmas no campo de seleção
async function carregarTurmas() {
    const campo = document.getElementById("turma_id");
    const turmaSelecionada = campo.value;
    const mensagem = document.getElementById("mensagem-aluno");

    try {
        const resposta = await fetch("/turmas");

        if (!resposta.ok) {
            throw new Error("Não foi possível carregar as turmas.");
        }

        const turmas = await resposta.json();
        campo.replaceChildren();

        const opcaoVazia = document.createElement("option");
        opcaoVazia.value = "";
        opcaoVazia.textContent = "Sem turma";
        campo.appendChild(opcaoVazia);

        turmas.forEach((turma) => {
            const opcao = document.createElement("option");
            opcao.value = turma.id;
            opcao.textContent = `${turma.nome} — ${turma.ano_letivo}`;
            campo.appendChild(opcao);
        });

        if ([...campo.options].some(
            (opcao) => opcao.value === turmaSelecionada
        )) {
            campo.value = turmaSelecionada;
        }
    } catch (erro) {
        mostrarMensagem(mensagem, "Erro ao carregar turmas: " + erro.message, "erro");
    }
}

// Cadastrar aluno
document.getElementById("form-aluno").addEventListener(
    "submit",
    async (evento) => {
        evento.preventDefault();

        const nome = document.getElementById("nome").value.trim();
        const matricula = document.getElementById("matricula").value.trim();
        const turmaId = document.getElementById("turma_id").value;
        const mensagem = document.getElementById("mensagem-aluno");

        const parametros = new URLSearchParams({ nome, matricula });

        if (turmaId) {
            parametros.append("turma_id", turmaId);
        }

        try {
            const resposta = await fetch(`/alunos?${parametros}`, {
                method: "POST"
            });

            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(
                    dados.detail || "Não foi possível cadastrar o aluno."
                );
            }

            mostrarMensagem(mensagem, dados.mensagem, "sucesso");
            evento.target.reset();

            await carregarTurmas();
            await listarAlunos();
        } catch (erro) {
            mostrarMensagem(mensagem, "Erro: " + erro.message, "erro");
        }
    }
);

// Listar alunos em uma tabela (com busca por nome ou matrícula)
let alunosCarregados = [];
let mapaTurmasAlunos = new Map();

async function listarAlunos() {
    const lista = document.getElementById("lista-alunos");
    lista.textContent = "Carregando alunos...";

    try {
        const [respostaAlunos, respostaTurmas] = await Promise.all([
            fetch("/alunos"),
            fetch("/turmas")
        ]);

        if (!respostaAlunos.ok || !respostaTurmas.ok) {
            throw new Error("Falha ao buscar alunos ou turmas.");
        }

        alunosCarregados = await respostaAlunos.json();
        const turmas = await respostaTurmas.json();

        mapaTurmasAlunos = new Map(
            turmas.map((turma) => [turma.id, turma.nome])
        );

        renderizarAlunos();
    } catch (erro) {
        lista.textContent = "Erro ao carregar alunos: " + erro.message;
    }
}

function renderizarAlunos() {
    const lista = document.getElementById("lista-alunos");
    const campoBusca = document.getElementById("busca-aluno");
    const termo = campoBusca ? campoBusca.value.trim().toLowerCase() : "";

    const filtrados = alunosCarregados.filter((aluno) =>
        aluno.nome.toLowerCase().includes(termo) ||
        String(aluno.matricula).toLowerCase().includes(termo)
    );

    lista.replaceChildren();

    if (alunosCarregados.length === 0) {
        lista.textContent = "Nenhum aluno cadastrado.";
        return;
    }

    if (filtrados.length === 0) {
        lista.textContent = "Nenhum aluno encontrado para essa busca.";
        return;
    }

    const tabela = document.createElement("table");
    tabela.className = "tabela-alunos";

    const cabecalho = document.createElement("thead");
    const linhaCabecalho = document.createElement("tr");

    ["Nome", "Matrícula", "Turma", "Situação"].forEach((titulo) => {
        const th = document.createElement("th");
        th.textContent = titulo;
        th.scope = "col";
        linhaCabecalho.appendChild(th);
    });

    cabecalho.appendChild(linhaCabecalho);
    tabela.appendChild(cabecalho);

    const corpo = document.createElement("tbody");

    filtrados.forEach((aluno) => {
        const linha = document.createElement("tr");

        const nomeTurma = aluno.turma_id
            ? mapaTurmasAlunos.get(aluno.turma_id) || "Turma não encontrada"
            : "Sem turma";

        [aluno.nome, aluno.matricula, nomeTurma].forEach((valor) => {
            const celula = document.createElement("td");
            celula.textContent = valor;
            linha.appendChild(celula);
        });

        const celulaStatus = document.createElement("td");
        const selo = document.createElement("span");
        selo.className = "status-aluno " +
            (aluno.ativo ? "status-ativo" : "status-inativo");
        selo.textContent = aluno.ativo ? "Ativo" : "Inativo";
        celulaStatus.appendChild(selo);
        linha.appendChild(celulaStatus);

        corpo.appendChild(linha);
    });

    tabela.appendChild(corpo);
    lista.appendChild(tabela);
}

const campoBuscaAluno = document.getElementById("busca-aluno");

if (campoBuscaAluno) {
    campoBuscaAluno.addEventListener("input", renderizarAlunos);
}

// ---------- Turmas ----------
// Cadastrar turma
document.getElementById("form-turma").addEventListener(
    "submit",
    async (evento) => {
        evento.preventDefault();

        const nome = document.getElementById("nome-turma").value.trim();
        const ano = document.getElementById("ano-letivo").value;
        const mensagem = document.getElementById("mensagem-turma");

        const parametros = new URLSearchParams({
            nome,
            ano_letivo: ano
        });

        try {
            const resposta = await fetch(`/turmas?${parametros}`, {
                method: "POST"
            });

            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(
                    dados.detail || "Não foi possível cadastrar a turma."
                );
            }

            mostrarMensagem(mensagem, dados.mensagem, "sucesso");
            evento.target.reset();

            await listarTurmas();
        } catch (erro) {
            mostrarMensagem(mensagem, "Erro: " + erro.message, "erro");
        }
    }
);

// Listar turmas
async function listarTurmas() {
    const lista = document.getElementById("lista-turmas");

    try {
        const resposta = await fetch("/turmas");

        if (!resposta.ok) {
            throw new Error("Falha ao buscar turmas.");
        }

        const turmas = await resposta.json();
        lista.replaceChildren();

        if (turmas.length === 0) {
            lista.textContent = "Nenhuma turma cadastrada.";
            return;
        }

        turmas.forEach((turma) => {
            const item = document.createElement("p");

            item.textContent =
                `${turma.nome} — Ano letivo: ${turma.ano_letivo} — ` +
                `ID: ${turma.id}`;

            lista.appendChild(item);
        });
    } catch (erro) {
        lista.textContent = "Erro ao carregar turmas: " + erro.message;
    }
}

// ---------- Início ----------
// A Visão geral é a primeira tela: carrega os números ao abrir a página.
carregarResumo();