# Aplicação: risco de agravamento de defasagem

Aplicação Streamlit que disponibiliza o modelo treinado no notebook
`notebooks/03_modelo_risco.ipynb`.

## Execução local

```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

## Publicação no Streamlit Community Cloud

1. Envie o repositório para o GitHub. O arquivo `.joblib` precisa ser
   versionado junto, e seu tamanho de 3,8 KB não representa problema.
2. Acesse share.streamlit.io e selecione "New app".
3. Informe o caminho do arquivo principal: `app/streamlit_app.py`
4. Informe o arquivo de dependências: `app/requirements.txt`
5. Conclua a publicação.

## Estrutura

```
app/
├── streamlit_app.py              # aplicação
├── requirements.txt              # versões fixas
├── README.md
├── .streamlit/config.toml        # tema e limite de upload
└── artifacts/
    └── modelo_risco.joblib       # modelo e distribuições de referência
```

## Conteúdo do arquivo de modelo

O arquivo não contém apenas o modelo. Como as variáveis preditoras são
percentis calculados dentro de cada ano, a aplicação precisa converter nota em
percentil, o que exige as distribuições de referência.

| Chave | Finalidade |
|---|---|
| `modelo` | Pipeline do scikit-learn já treinado |
| `features` | Ordem das colunas, à qual o modelo é sensível |
| `quantis` | Percentis de 0 a 100 de cada indicador, usados na conversão |
| `idade_mediana_por_fase_ideal` | Base para derivar `idade_rel_fase_ideal` |
| `base_rate` | Taxa de eventos por estrato, usada na classificação relativa |
| `metricas` | Valores exibidos na aba de documentação |
| `faixas` | Limites aplicados na validação das entradas |

## Formato do arquivo CSV para o modo em lote

Colunas obrigatórias: `ra`, `fase`, `fase_ideal`, `idade`, `tempo_casa`,
`rede_publica`, `genero_f`

Colunas opcionais: `iaa`, `ieg`, `ips`, `ida`, `ipv`. Quando ausentes, o modelo
trata o campo como não informado.

O arquivo modelo pode ser baixado diretamente na aplicação.

## Validações implementadas

**Consulta individual**

- Indicadores no intervalo de 0 a 10
- Fase e fase ideal no intervalo de 0 a 8
- Idade entre 5 e 25 anos
- Diferença entre fase e fase ideal no intervalo de -5 a +3, faixa observada na
  base histórica
- Tempo de programa não negativo

**Arquivo CSV**

- Presença de todas as colunas obrigatórias
- Arquivo com ao menos uma linha de dados
- Ausência de registros de RA repetidos
- Tipos numéricos corretos nas colunas quantitativas
- Linhas fora das faixas são descartadas com aviso ao usuário, nunca de forma
  silenciosa

## Boas práticas adotadas

**Versões fixas no arquivo de dependências.** A biblioteca joblib não garante
compatibilidade entre versões distintas do scikit-learn. Caso o arquivo do
modelo seja gerado novamente com outra versão, é necessário atualizar a
especificação correspondente, sob risco de falha na publicação com mensagem
pouco informativa.

**Uso de `@st.cache_resource` no carregamento.** O modelo é carregado uma única
vez por sessão do contêiner. A função `cache_data` seria inadequada, pois o
objeto não é serializável para cache de dados.

**Falha explícita em vez de silenciosa.** A ausência do arquivo de modelo ou
sua incompatibilidade produzem mensagens que orientam a correção, e não um
rastreamento de erro bruto.

**Nenhum dado de aluno permanece no repositório.** A aplicação não persiste
informações. O arquivo CSV enviado existe apenas durante a sessão, e o diretório
`data/raw/` está listado em `.gitignore`.

**Limite de upload em 5 MB.** Um arquivo com dados de turma fica bem abaixo
desse valor.

**A aplicação não realiza treinamento.** O Community Cloud oferece cerca de
1 GB de memória e reinicia contêineres sem aviso prévio, o que torna o
treinamento em tempo de execução desnecessário e frágil.

## Manutenção

Para incorporar dados de 2025:

1. Acrescente a aba `PEDE2025` à planilha em `data/raw/`
2. Inclua o ano em `config.yaml`, na chave `dados.anos`
3. Execute os notebooks 01, 02 e 03
4. Substitua o arquivo `app/artifacts/modelo_risco.joblib`
5. Verifique se a versão do scikit-learn corresponde à indicada em
   `requirements.txt`

Os contratos definidos em `src/data/validate.py` interrompem a execução caso a
estrutura da nova aba divirja do esperado, que é o comportamento desejado.
