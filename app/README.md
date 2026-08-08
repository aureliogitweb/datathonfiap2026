# Aplicação: risco de agravamento de defasagem

App em Streamlit que disponibiliza o modelo treinado no notebook
`notebooks/03_modelo_risco.ipynb`.

## Rodando localmente

```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

## Publicando no Streamlit Community Cloud

1. Suba o repositório no GitHub. O arquivo `.joblib` precisa ir junto, e como
   tem só 3,8 KB não atrapalha.
2. Entre em share.streamlit.io e clique em "New app".
3. Main file path: `app/streamlit_app.py`
4. Requirements: `app/requirements.txt`
5. Deploy.

## Estrutura

```
app/
├── streamlit_app.py              # a aplicação
├── requirements.txt              # versões fixas
├── exemplo_turma.csv             # 18 alunos para teste
├── README.md
├── .streamlit/config.toml        # tema e limite de upload
└── artifacts/
    └── modelo_risco.joblib       # modelo e distribuições de referência
```

## O que tem dentro do arquivo do modelo

Não é só o modelo. Como as variáveis são percentis calculados dentro de cada
ano, o app precisa converter nota em percentil, e para isso carrega as
distribuições de referência junto.

| Chave | Para que serve |
|---|---|
| `modelo` | O pipeline do scikit-learn já treinado |
| `features` | A ordem das colunas, que o modelo leva a sério |
| `quantis` | Percentis de 0 a 100 de cada indicador, usados na conversão |
| `idade_mediana_por_fase_ideal` | Deriva a variável de idade relativa |
| `base_rate` | Taxa de eventos por estrato, para classificar o risco relativo |
| `metricas` | Os números que aparecem na aba de documentação |
| `faixas` | Limites usados na validação das entradas |

## Formato do CSV para o modo em lote

Obrigatórias: `ra`, `fase`, `fase_ideal`, `idade`, `tempo_casa`,
`rede_publica`, `genero_f`

Opcionais: `iaa`, `ieg`, `ips`, `ida`, `ipv`. Se faltarem, o modelo trata como
não informado.

Dá para baixar um arquivo modelo direto pela aplicação.

### Turma de exemplo

O `app/exemplo_turma.csv` tem 18 alunos fictícios e serve para testar sem
precisar montar planilha. Os perfis cobrem os dois estratos e dão risco entre
0,8% e 47,3%.

Vale reparar num detalhe que parece errado mas não é: os dois alunos de menor
risco no arquivo estão defasados em uma fase, enquanto os de maior risco estão
em dia. É efeito de piso, porque quem já acumulou defasagem tem menos margem
para piorar. O app mostra um aviso explicando isso quando o caso aparece.

## Validações

Na consulta individual

- Indicadores entre 0 e 10
- Fase e fase ideal entre 0 e 8
- Idade entre 5 e 25 anos
- Diferença entre fase e fase ideal entre -5 e +3, que é a faixa que existe na
  base
- Tempo de programa não negativo

No CSV

- Todas as colunas obrigatórias presentes
- Pelo menos uma linha de dados
- Nenhum RA repetido
- Colunas numéricas com tipo certo
- Linhas fora das faixas são descartadas com aviso na tela.

## Cuidados que tomei

Versões fixas no requirements. O joblib não garante compatibilidade entre
versões diferentes de scikit-learn. Se você regerar o modelo com outra versão,
vai precisar atualizar aqui caso contrário vai quebrar.

`@st.cache_resource` no carregamento. O modelo carrega uma vez só por
sessão. Usar `cache_data` daria errado, porque o objeto não é serializável para
cache de dados.

Erro que fala. Se o arquivo do modelo sumir ou for incompatível, o app diz
o que fazer em vez de despejar um stack trace na cara do usuário.

Nenhum dado de aluno fica guardado. O app não persiste nada, o CSV enviado
vive só na sessão, e o `data/raw/` está no `.gitignore`.

Upload limitado a 5 MB. Uma planilha de turma fica bem abaixo disso.

O app não treina nada. O Community Cloud tem cerca de 1 GB de memória e
reinicia contêiner sem avisar. Treinar em tempo de execução seria desnecessário.

## Manutenção

Para incluir os dados de 2025:

1. Adicione a aba `PEDE2025` na planilha em `data/raw/`
2. Coloque o ano no `config.yaml`, em `dados.anos`
3. Rode os notebooks 01, 02 e 03
4. Substitua o `app/artifacts/modelo_risco.joblib`
5. Confira se a versão do scikit-learn bate com o `requirements.txt`

Os contratos do `src/data/validate.py` quebram na hora se a estrutura da aba
nova vier diferente, que é justamente o que queremos.
