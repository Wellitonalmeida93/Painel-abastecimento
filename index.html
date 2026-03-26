<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Painel BI Abastecimento</title>

<style>
body {
    font-family: Arial;
    background: #0f172a;
    color: white;
    padding: 20px;
}

h1 {
    margin-bottom: 20px;
}

input {
    padding: 8px;
    margin: 5px;
    border-radius: 6px;
    border: none;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

th, td {
    padding: 10px;
    border-bottom: 1px solid #334155;
}

th {
    background: #1e293b;
}

td {
    text-align: right;
}

td.texto {
    text-align: left;
}
</style>
</head>

<body>

<h1>📊 Painel Abastecimento</h1>

<input id="filtroPlaca" placeholder="Placa">
<input id="filtroCidade" placeholder="Cidade">

<table>
<thead>
<tr>
<th>Data</th>
<th>Hora</th>
<th>Placa</th>
<th>Posto</th>
<th>Cidade</th>
<th>UF</th>
<th>Produto</th>
<th>Litros</th>
<th>Total</th>
<th>Litro</th>
</tr>
</thead>
<tbody id="tabela"></tbody>
</table>

<script>
let dados = [];

// 🔹 FORMATAR
function moeda(v) {
    return Number(v || 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function numero(v) {
    return Number(v || 0).toLocaleString("pt-BR", {
        minimumFractionDigits: 2
    });
}

// 🔹 BUSCAR API
fetch("https://painel-abastecimento-api.onrender.com/api/transacoes")
.then(r => r.json())
.then(res => {
    dados = res.dados || [];
    render(dados);
});

// 🔹 RENDER
function render(lista) {
    const tabela = document.getElementById("tabela");
    tabela.innerHTML = "";

    lista.forEach(i => {

        let data = "";
        let hora = "";

        if (i.dataTransacao) {
            const dt = new Date(i.dataTransacao);
            data = dt.toLocaleDateString("pt-BR");
            hora = dt.toLocaleTimeString("pt-BR");
        }

        tabela.innerHTML += `
        <tr>
            <td>${data}</td>
            <td>${hora}</td>
            <td class="texto">${i.placa || ""}</td>
            <td class="texto">${i.nomeReduzidoEstabelecimento || ""}</td>
            <td class="texto">${i.nomeCidade || ""}</td>
            <td>${i.uf || ""}</td>
            <td class="texto">${i.tipoCombustivel || ""}</td>
            <td>${numero(i.litros)}</td>
            <td>${moeda(i.valorTransacao)}</td>
            <td>${moeda(i.valorLitro)}</td>
        </tr>`;
    });
}

// 🔹 FILTROS
document.getElementById("filtroPlaca").addEventListener("input", filtrar);
document.getElementById("filtroCidade").addEventListener("input", filtrar);

function filtrar() {
    const placa = filtroPlaca.value.toLowerCase();
    const cidade = filtroCidade.value.toLowerCase();

    const filtrado = dados.filter(i =>
        (i.placa || "").toLowerCase().includes(placa) &&
        (i.nomeCidade || "").toLowerCase().includes(cidade)
    );

    render(filtrado);
}
</script>

</body>
</html>
