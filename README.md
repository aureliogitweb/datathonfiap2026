# Datathon Passos Mágicos: previsão do risco de agravamento da defasagem

Neste trabalho analisei os dados da Pesquisa Extensiva do Desenvolvimento Educacional (PEDE) da Associação Passos Mágicos, referentes aos anos de 2022, 2023 e 2024. O objetivo foi entender a evolução dos alunos ao longo do programa, responder às perguntas propostas no desafio e desenvolver um modelo capaz de estimar a probabilidade de um aluno apresentar agravamento da defasagem, além de disponibilizar essa previsão em uma aplicação para apoiar a equipe pedagógica.

A base utilizada contém informações de **1.661 alunos**, totalizando **3.030 registros aluno/ano** e **1.365 transições** entre um ano e outro.

## Principais resultados

1. O programa apresenta resultados positivos, mesmo em um cenário conservador

Entre os **468 alunos que participaram dos três anos analisados**, a proporção de estudantes classificados no nível adequado passou de **32,7% para 65,2%**. Individualmente, **58,8% dos alunos melhoraram**, enquanto **10,3% apresentaram piora**.

Também testei um cenário bastante conservador utilizando os limites de Manski, assumindo que todos os **509 alunos que deixaram o programa** tivessem piorado. Mesmo nessa hipótese extrema, a melhora entre os ciclos continua aparecendo. A evolução mínima estimada foi de **9,4 pontos percentuais**, muito próxima dos **10,1 pontos** observados na base original. Além disso, o limite inferior do segundo ciclo (**30,9%**) ainda supera o resultado observado no primeiro (**30,8%**).

Esses resultados reforçam que a melhora observada não depende apenas dos alunos que permaneceram no programa.



2. O IAN não representa exatamente o que seu nome sugere

Ao analisar o Indicador de Adequação ao Nível (IAN), percebi que ele não é um indicador construído a partir de uma avaliação independente. Na prática, ele é apenas uma recodificação da defasagem em três valores possíveis (10, 5 e 2,5).

Além disso, a própria defasagem corresponde quase exatamente ao cálculo entre a **fase atual** e a **fase ideal**, coincidindo em **99,93% dos registros**.

Quando aprofundei essa análise, encontrei um padrão bastante claro: **98,7% das pioras** aconteceram porque o aluno permaneceu na mesma fase enquanto a fase ideal avançou naturalmente com o tempo.

Entre os alunos que não foram promovidos de fase, aproximadamente **53% pioraram**. Já entre os promovidos, apenas **0,3%** apresentaram piora.

Na prática, isso indica que o chamado "risco de defasagem" representa muito mais um desalinhamento entre a progressão esperada pelo programa e a progressão escolar do que uma queda real de desempenho acadêmico.


### 3. Os alunos com menor desempenho tendem a superestimar seus próprios resultados

Ao comparar a autoavaliação dos alunos (IAA) com o desempenho acadêmico (IDA), encontrei uma relação muito fraca.

| Quintil          | IDA médio | Autoavaliação |
| ---------------- | --------: | ------------: |
| Menor desempenho |      3,54 |          8,50 |
| Maior desempenho |      8,85 |          8,92 |

A correlação de Spearman entre esses indicadores foi de apenas **0,135**, mostrando que alunos com baixo desempenho costumam avaliar seu próprio desempenho de forma bastante semelhante aos alunos com melhores resultados.

Isso sugere que estratégias baseadas apenas na procura espontânea por ajuda provavelmente deixam de alcançar justamente quem mais precisa de acompanhamento.



### 4. A evasão é um problema diferente da defasagem

Entre **25% e 30% dos alunos deixam o programa a cada ano**, e praticamente não retornam. Em toda a base, apenas **quatro alunos** voltaram após um período de ausência.

Também observei que o **IEG (Indicador de Engajamento)** é um excelente preditor de evasão (p = 7 × 10⁻¹⁴), mas praticamente não consegue prever o agravamento da defasagem (AUC = 0,523).

Esse resultado mostra que evasão e agravamento da defasagem são fenômenos diferentes e precisam ser tratados com estratégias de acompanhamento distintas.



5. Os alunos que já apresentam melhores condições parecem aproveitar mais o programa

Ao comparar alunos que iniciaram com a mesma defasagem (-2), observei que aqueles classificados como **Ametista** avançaram, em média, **1,35 fase**, enquanto os classificados como **Quartzo** avançaram apenas **0,30 fase**.

Esse comportamento é compatível com o chamado **efeito Mateus**, em que quem já possui melhores condições tende a aproveitar mais as oportunidades oferecidas.

No entanto, esse resultado deve ser interpretado com cautela, pois a quantidade de alunos Quartzo acompanhados durante todo o período foi pequena (**30 casos**).


# Modelo preditivo

O modelo foi desenvolvido para prever se um aluno apresentaria agravamento da defasagem entre um ciclo e o seguinte.

O evento previsto foi definido como:

> **defasagem(t+1) < defasagem(t)**

Esse evento ocorreu em **17,3% das transições**, mantendo praticamente a mesma frequência nas duas janelas analisadas.

Para evitar vazamento de dados, utilizei as transições de **2022→2023** para treinamento e **2023→2024** para teste. Durante a validação utilizei **GroupKFold**, agrupando os registros pelo RA, já que **468 alunos aparecem nas duas janelas** e uma divisão aleatória faria o mesmo aluno aparecer simultaneamente no treino e no teste.

## Comparação dos modelos

| Modelo                       | PR-AUC | Brier |
| ---------------------------- | -----: | ----: |
| Random Forest                |  0,657 | 0,152 |
| XGBoost                      |  0,620 | 0,100 |
| Regressão Logística          |  0,557 | 0,107 |
| LightGBM                     |  0,525 | 0,113 |
| Árvore de Decisão            |  0,410 | 0,125 |
| Regra baseada apenas na fase |  0,363 | 0,116 |

Embora o **Random Forest** tenha apresentado o maior PR-AUC geral, esse resultado é influenciado pela diferença na frequência de eventos entre as fases iniciais e avançadas.

Quando avaliei apenas os alunos em fase avançada cenário em que a simples informação da fase deixa de ser suficiente  a **Regressão Logística** apresentou o melhor desempenho (**PR-AUC = 0,326**).

Como os intervalos de confiança dos modelos se sobrepõem, utilizei o critério definido antes da modelagem: em caso de empate estatístico, priorizar o modelo mais simples, mais interpretável e melhor calibrado.

Também avaliei a calibração do modelo por meio do índice de **Brier (0,107)**. Os valores previstos ficaram próximos dos valores observados em todos os níveis de risco. Na prática, isso significa que, entre alunos com probabilidade prevista de aproximadamente **30%**, cerca de **30% realmente apresentaram agravamento da defasagem**, tornando as probabilidades úteis para apoiar a tomada de decisão da equipe pedagógica.

Considerando apenas os alunos em fase avançada, selecionar os **30 estudantes com maior risco previsto** permitiu identificar **3,7 vezes mais casos** do que uma regra simples baseada apenas na fase.

Entre todas as variáveis analisadas, o **IPV** foi o principal fator de proteção, apresentando uma razão de chances de **0,46**. Além de ter o maior impacto observado, é um indicador sobre o qual a instituição pode atuar diretamente, tornando-se um dos principais pontos de atenção para futuras intervenções.


Como executar
```bash
git clone <url-do-repositorio>
cd passos-magicos-datathon

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# coloque a planilha PEDE em data/raw/. O nome do arquivo não importa,
# pois o carregador localiza qualquer arquivo .xlsx presente na pasta.
jupyter lab
```
Execute os notebooks na ordem 01, 02 e 03. O terceiro gera o arquivo do modelo
consumido pela aplicação.
```bash
streamlit run app/streamlit_app.py
```
Aplicação publicada: (inserir a URL do Community Cloud após o deploy)
Para ambientes conda: `conda env create -f environment.yml && conda activate passos-datathon`
---
Estrutura do repositório
```
passos-magicos-datathon/
├── README.md
├── LICENSE
├── requirements.txt
├── environment.yml
├── config.yaml                     
├── .gitignore
│
├── data/
│   ├── raw/                         
│   ├── interim/                    
│   └── processed/
│
├── notebooks/
│   ├── 01_qualidade_dados.ipynb     # auditoria de drift, zeros e contratos
│   ├── 02_eda_perguntas.ipynb       # as 11 perguntas do enunciado
│   └── 03_modelo_risco.ipynb        # entregável principal do modelo
│
├── src/
│   ├── data/
│   │   ├── load.py                  
│   │   ├── clean.py                 
│   │   └── validate.py              
│   ├── features/build.py            
│   ├── models/
│   │   ├── train.py                 # pipelines dos cinco modelos
│   │   └── evaluate.py              # PR-AUC, calibração e recall por faixa
│   └── analysis/eda_tecnica.py      # drift, VIF, deslocamento e fluxo
│
├── app/
│   ├── streamlit_app.py             # abas de lote, individual e documentação
│   ├── requirements.txt
│   ├── README.md
│   └── artifacts/modelo_risco.joblib
│
├── reports/
│   ├── figures/
│   └── *.csv                        # coeficientes, drift e deslocamento
│
└── docs/
    ├── decisoes_tecnicas.md         # registro de decisões e revisões
    └── quadro_hipoteses.csv         # 20 hipóteses com seus vereditos
```
Decisões metodológicas

Durante o desenvolvimento do projeto, tomei algumas decisões para garantir que o modelo fosse confiável e que os resultados refletissem o comportamento real dos dados.

**Prevenção de vazamento de dados (data leakage).**
Algumas variáveis da base são derivadas umas das outras. A sequência **Fase → Fase Ideal → Defasagem → IAN → INDE → Pedra** é determinística, ou seja, conhecer uma delas praticamente revela as demais. Por esse motivo, não utilizei **IAN**, **INDE** e **Pedra** como variáveis preditoras. Além disso, implementei uma validação no módulo `src/features/build.py` que interrompe a execução caso alguma dessas variáveis seja utilizada ou caso qualquer variável apresente correlação superior a 0,9 com a variável alvo.

**Padronização do IPS por ano.**
Ao analisar o IPS, observei uma mudança significativa entre os anos. Na coorte fechada, o indicador varia de **7,50 para 5,00** e depois retorna para **7,51**, mesmo com praticamente os mesmos alunos. Isso indica que a alteração ocorreu na forma de cálculo do indicador e não no perfil da população. Para reduzir esse efeito, utilizei o IPS em formato de **percentil dentro de cada ano**, tornando a comparação menos sensível às mudanças de escala.

**Tratamento dos valores iguais a zero.**
Cada indicador foi tratado de acordo com seu comportamento na base. No caso do **IAA**, existe uma lacuna na distribuição entre **0 e 1,7**, e os valores iguais a zero não permanecem ao longo dos anos, indicando que provavelmente representam ausência de resposta. Por isso, esses registros foram convertidos para valores ausentes. Já os indicadores **IEG** e **IDA** apresentam distribuição contínua, e seus valores iguais a zero representam observações válidas, sendo mantidos na base.

**Não utilização de SMOTE.**
Optei por não utilizar técnicas de sobreamostragem, como o SMOTE. Embora apenas **17,3% das transições** correspondam ao evento de interesse, essa proporção ainda é suficiente para o treinamento do modelo. Além disso, como o objetivo é prever probabilidades, a criação de exemplos sintéticos poderia alterar a distribuição real dos dados e prejudicar a calibração do modelo.

**Validação da integridade dos dados.**
Também desenvolvi um módulo de validação (`src/data/validate.py`) para verificar automaticamente a integridade da base antes do treinamento. Esse módulo valida a unicidade das chaves, a consistência da defasagem, os limites esperados para cada indicador e a cobertura dos dados por ano. Todos esses testes foram executados utilizando cenários de corrupção proposital dos dados e identificaram corretamente as inconsistências inseridas.

Limitações

Este trabalho também apresenta algumas limitações que devem ser consideradas na interpretação dos resultados.

O modelo desenvolvido prevê o **agravamento da defasagem** conforme ela é definida na base de dados. Como essa defasagem representa principalmente um descompasso entre a fase do aluno e a fase considerada ideal pelo programa, o modelo não deve ser interpretado como um preditor direto do desempenho pedagógico.

A análise foi realizada apenas com os alunos que permaneceram na base de dados. Como entre **25% e 30% dos estudantes deixam o programa a cada ano**, os resultados não necessariamente representam toda a população atendida pela instituição.

Outra limitação é que os dados não permitem identificar se um aluno deixou de avançar por motivos pedagógicos ou administrativos. Dessa forma, não foi possível separar essas duas situações durante a análise.

O indicador **IPP** não foi utilizado na modelagem porque não está disponível para o ano de 2022. Testes adicionais mostraram que sua inclusão não alteraria de forma significativa o desempenho do modelo quando consideradas as demais variáveis disponíveis.

Além disso, os resultados obtidos mostram **associações estatísticas**, e não relações de causa e efeito. Como não existe um grupo de controle, não é possível afirmar que as mudanças observadas foram causadas exclusivamente pelo programa.

Por fim, houve uma alteração na definição da **Fase Ideal** entre 2022 e 2023. Nesse período, a fase **ALFA** passou de "2º e 3º ano" para "1º e 2º ano", tornando inadequadas comparações diretas dos níveis absolutos entre esses dois anos. Por esse motivo, essa mudança foi considerada durante toda a análise.

