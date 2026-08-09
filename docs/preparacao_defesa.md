# Preparação para a defesa

Trinta perguntas que uma banca rigorosa faria, com a resposta que sustenta o
trabalho. As respostas estão escritas como fala, não como texto técnico, porque
é assim que você vai precisar usá-las.

**Regra geral para a defesa:** quando a pergunta expõe uma limitação real,
reconheça primeiro e explique depois. Banca desconfia de quem defende tudo.

---

## Estatística

### 1. Vocês aplicaram limites de Manski. O limite de uma diferença é a diferença dos limites?

Não, e essa foi uma correção que a gente fez na auditoria final. A primeira
versão subtraía limite inferior de limite inferior, o que está errado. O limite
correto da diferença usa o melhor caso de uma janela contra o pior caso da
outra, e aí o intervalo vai de menos vinte e nove décimos a mais trinta e três
pontos, contendo zero.

Então a conclusão honesta é: a melhora **dentro** da coorte é medição direta e
inequívoca, com Wilcoxon p igual a sete vírgula cinco vezes dez elevado a menos
trinta e cinco. Já a comparação entre ciclos depende de a atrição ter sido
parecida nos dois anos, que foi trinta vírgula dois e vinte e quatro vírgula
seis por cento. É uma suposição razoável, não uma garantia.

### 2. Por que Wilcoxon pareado e não um teste t?

Porque a defasagem é ordinal, varia de menos cinco a mais três, e tem uma
concentração enorme em zero e menos um. Não é normal nem de longe. E como o
mesmo aluno aparece nos três anos, as observações não são independentes, então
qualquer teste que assuma independência subestima o erro padrão.

### 3. Vocês reportam p-valores muito pequenos, tipo 7e-14. Com mil e trezentas observações, isso não é trivial?

É justamente por isso que a gente reporta tamanho de efeito junto e não decide
nada só por p-valor. Com esse n, diferença irrelevante atinge significância.
No caso do engajamento e evasão, o que importa é a diferença absoluta: oito
vírgula oitenta e seis contra oito vírgula vinte e três. Pequena em pontos, mas
consistente e com AUC que separa os grupos.

### 4. Como vocês controlaram erro tipo I com tantos testes?

Separamos em famílias. As hipóteses confirmatórias, que eram três e estavam
pré-especificadas, não receberam correção porque têm replicação independente
entre as duas janelas. As exploratórias, que eram dez, passaram por
Benjamini-Hochberg com FDR de dez por cento. Sete sobreviveram, e as três que
caíram já eram não significantes antes da correção. Ou seja, nenhuma conclusão
mudou de status.

### 5. A base rate do alvo é 17,3% nas duas janelas. Isso não é bom demais para ser verdade?

A gente também estranhou. A explicação é mecânica: a piora acontece quando o
aluno não é promovido e a fase ideal avança. Não promoção acontece em cerca de
trinta e dois por cento dos casos, e a régua avança em cerca de cinquenta e dois
por cento. O produto dá dezessete por cento, que é exatamente a base rate. São
dois processos estruturais e estáveis, então a taxa constante faz sentido.

### 6. O efeito Mateus está baseado em quantos alunos?

Dez alunos Quartzo nesse recorte específico. Por isso reportamos como indício e
não como conclusão, e o slide diz isso explicitamente. Não faria sentido omitir,
porque se confirmar é o achado mais importante para o desenho do programa, mas
seria desonesto apresentar como fato.

---

## Machine Learning

### 7. Por que o IAN não entrou como variável preditora?

Porque o IAN não é uma avaliação. Ele é a defasagem recodificada em dez, cinco
ou dois vírgula cinco, num mapeamento determinístico que confere nos três anos.
Usar o IAN para prever defasagem seria prever a variável com ela mesma. O modelo
daria AUC perto de um e não valeria nada.

### 8. E o INDE? Ele tem outros indicadores dentro.

O INDE tem, mas também carrega o IAN com peso zero vírgula dez. A gente
recuperou os pesos por regressão e deu R quadrado igual a um, exato. Então o
INDE contém o alvo. Ficou proibido, junto com Pedra, que é só um agrupamento do
INDE.

### 9. Vocês usam percentil calculado dentro de cada ano. Isso não é vazamento, já que usa dados de teste?

Usa a distribuição do ano inteiro, incluindo alunos do conjunto de teste, mas
nenhuma informação sobre o alvo atravessa. Em uso real, quando a coordenação for
pontuar a turma de 2025, a coorte inteira de 2025 já existe antes de qualquer
previsão. É a mesma lógica que autoriza normalizar por lote em produção.

### 10. Por que GroupKFold e não validação cruzada normal?

Porque quatrocentos e sessenta e oito alunos aparecem nas duas janelas de
transição. Numa validação cruzada aleatória, o mesmo aluno cairia em treino e
validação, e o modelo teria visto aquela pessoa antes. O agrupamento por RA
impede isso.

### 11. O Random Forest teve PR-AUC maior. Por que vocês escolheram a logística?

Primeiro, porque o número global engana: a taxa de eventos é quarenta e oito por
cento na fase inicial e oito por cento na avançada, e só separar esses dois
grupos já produz PR-AUC alto sem prever nada. No estrato onde o modelo precisa
trabalhar, a logística fica em zero vírgula trezentos e vinte e seis e o Random
Forest em zero vírgula duzentos e sessenta e dois.

Mas seria desonesto chamar isso de vitória. A diferença é mais zero vírgula
cinquenta e sete, com intervalo de confiança cruzando o zero e p igual a zero
vírgula vinte e cinco. Eles empatam. O que decidiu foi um critério que a gente
definiu antes de rodar: em empate, fica o mais simples e mais bem calibrado.

### 12. Com cento e quatro eventos no treino e treze variáveis, não há overfitting?

A regra prática é dez eventos por parâmetro, o que daria um teto de dez a quinze
variáveis. Estamos no limite, e por isso usamos regularização e grade de
hiperparâmetros pequena de propósito. Grade grande com esse n seleciona a
combinação que melhor se ajusta ao ruído da validação, que é overfitting no
processo de seleção e não no ajuste.

O teste real é o desempenho fora do tempo, em dados que o modelo nunca viu, e
ele se sustentou.

### 13. Por que PR-AUC e não acurácia ou ROC?

Com dezessete por cento de eventos, um modelo que diz sempre "não" acerta oitenta
e três por cento. Acurácia não serve. E a ROC-AUC infla quando há muitos
negativos verdadeiros fáceis. PR-AUC foca na classe minoritária, que é justamente
quem a instituição precisa encontrar.

### 14. Por que não usaram SMOTE, já que a classe é desbalanceada?

Porque a dezessete por cento o problema não é falta de exemplos positivos, é
calibração. O enunciado pede uma probabilidade, e o app mostra um percentual
para um educador decidir. Casos sintéticos distorcem exatamente essa
probabilidade. Aliás, a gente também removeu o class_weight balanced pelo mesmo
motivo: ele melhorava o ranking e destruía a calibração, com Brier indo a zero
vírgula cento e setenta e nove, pior que a regra trivial.

### 15. Como vocês verificaram a calibração?

Dividimos as previsões em quintis e comparamos o previsto com o observado em
cada faixa. Bateu em todas: o modelo prevê dois vírgula oito por cento e
observamos dois vírgula zero; prevê quarenta e sete vírgula cinco e observamos
quarenta e nove. O Brier ficou em zero vírgula cento e sete. Testamos aplicar
Platt por cima e não melhorou, o que faz sentido porque a log-loss já é uma
regra de pontuação própria.

### 16. Quanto do desempenho vem só da defasagem e da fase?

Boa parte. Um modelo só com essas duas variáveis dá zero vírgula duzentos e
sessenta e quatro no estrato avançada, e o conjunto completo com treze variáveis
dá zero vírgula trezentos e vinte e sete. As outras onze acrescentam zero vírgula
zero sessenta e três.

Isso não é um defeito escondido, é a conclusão do trabalho: o fenômeno é
majoritariamente estrutural. E é por isso que a recomendação principal é rever a
sincronia entre fase e ano escolar, não perseguir aluno individualmente.

### 17. O IPV é o principal fator de proteção. Vocês verificaram se ele não é circular?

Verificamos, e é a limitação mais séria do modelo. O IPV é também o melhor
preditor isolado da promoção de fase, com AUC de zero vírgula seiscentos e
setenta e nove, que é justamente a decisão que gera o alvo. Se a coordenação
consulta o IPV ao decidir promoções, parte da previsão é circular.

A gente não consegue verificar isso com os dados que tem, e por isso deixou
declarado no relatório e na própria aplicação. Seria uma pergunta direta para a
instituição.

### 18. O modelo publicado é o mesmo que vocês avaliaram?

Não exatamente, e isso está declarado. As métricas vêm do modelo treinado só em
2022 para 2023. O modelo publicado foi retreinado com todos os dados, que é
prática usual em produção porque mais dados costumam ajudar, mas significa que
os números descrevem a validação e não literalmente a versão em uso.

---

## Engenharia de Dados

### 19. Como vocês garantem que não houve vazamento?

Tem uma função de auditoria que roda antes do treino e levanta exceção em dois
casos: se alguma variável proibida entrar na matriz, ou se qualquer variável
tiver correlação acima de zero vírgula nove com o alvo. A maior correlação que
encontramos foi zero vírgula trezentos e oito, da própria defasagem.

Além disso, a função que monta as transições só traz três colunas do ano
seguinte, e isso está documentado no código.

### 20. A régua de Fase Ideal mudou entre 2022 e 2023. Isso não invalida tudo?

Invalida uma coisa específica: comparar nível absoluto de defasagem entre 2022 e
2023 na base completa. Por isso as análises longitudinais usam coorte fechada.

A gente também testou se a mudança contaminava o alvo, e não contamina. O
gradiente de risco por fase ideal é praticamente idêntico na janela em que a
régua ficou estável: quarenta e três vírgula oito por cento contra quarenta e
oito por cento. Se fosse artefato, apareceria só numa janela.

### 21. Como vocês decidiram quais zeros eram dados faltantes?

Por evidência, e a decisão acabou sendo diferente para cada indicador. No IAA há
uma lacuna na distribuição: depois do zero, o próximo valor é um vírgula sete.
Numa média de várias notas, valores intermediários existiriam se o zero fosse
real. E os zeros não persistem entre anos, o que descarta ser traço do aluno.
Viraram nulo.

Já o IEG e o IDA têm distribuição contínua, com zero, zero vírgula cinco, zero
vírgula sete. Ali o zero é medida real, então ficaram. A regra uniforme que a
gente tinha pensado no começo teria destruído cento e dez zeros legítimos do
IEG.

### 22. Como vocês sabem que a oscilação do IPS é mudança de instrumento e não dos alunos?

Três evidências. Primeiro, o teste roda na coorte fechada, com os mesmos
trezentos e trinta e dois alunos, então a composição não muda. Segundo, o padrão
é em V: sete vírgula cinco, cinco, sete vírgula cinco. População não faz isso.
Terceiro, o controle negativo: a defasagem se move com amplitude parecida, mas
em linha reta, porque é estrutural.

Ainda tem a prova documental da granularidade. O IEG tem setenta e cinco valores
distintos com uma casa decimal em 2022, e setecentos e quarenta e um valores com
dezesseis casas em 2024. Isso não se discute estatisticamente.

### 23. Vocês encontraram algum erro na base?

Vários, e o mais perigoso foi no nosso próprio código. O INDE de 2024 vinha como
texto, e o parser removia o ponto achando que era separador de milhar. O valor
oito vírgula trezentos e trinta e sete virou oito mil trezentos e trinta e sete,
e a média do ano foi para quinze. Só apareceu porque a validação olha
distribuição, não só esquema.

Outro foi o tamanho da turma. Em 2022 a coluna é só a letra, em 2023 e 2024 já
vem com a fase junto. Agrupando errado, o tamanho médio dava cinquenta e cinco
em 2022 e treze em 2024. Essa variável ia entrar no modelo e degradar em silêncio.

---

## Storytelling

### 24. Vocês abrem com "o programa funciona". Isso não é dizer o que o cliente quer ouvir?

A ordem é essa porque é a conclusão mais defensável e com medição mais direta.
Mas o segundo slide já derruba a premissa do próprio indicador que a instituição
usa, e o slide seis mostra que o programa beneficia menos justamente os alunos
mais vulneráveis. Se a gente quisesse agradar, teria parado no primeiro.

### 25. O deck afirma que o programa funciona. Isso é uma afirmação causal?

Não, e está declarado no penúltimo slide. Não existe grupo de controle na base.
A gente observa que os alunos melhoraram durante o período em que estavam no
programa, o que é diferente de afirmar que melhoraram por causa dele. Toda a
linguagem do relatório é associativa.

### 26. Por que a apresentação não mostra as curvas de avaliação do modelo?

Porque o público é gerencial e o vídeo tem cinco minutos. Curva precision-recall
não comunica nada para quem vai decidir orçamento. O que comunica é: entre os
trinta alunos priorizados, o modelo encontra onze casos e a regra óbvia encontra
três. As curvas estão no notebook, para quem quiser auditar.

### 27. Vocês apresentam a evasão como achado, mas o enunciado pedia defasagem. Não é fugir do escopo?

O enunciado pede defasagem no item nove, e no item onze pede explicitamente
insights adicionais. A evasão entra ali. E entra porque os dados mostram que é o
problema mais grave: vinte e cinco a trinta por cento saem por ano, só quatro
voltaram em três ciclos, e o sinal antecedente é mais forte que o do alvo
principal. O modelo pedido foi entregue; a evasão é o que a gente encontrou no
caminho.

---

## Streamlit

### 28. Por que a aplicação não treina o modelo?

Porque o Community Cloud tem cerca de um giga de memória e reinicia contêiner
sem avisar. Treinar em tempo de execução seria frágil e desnecessário: o artefato
serializado já tem tudo. O app carrega, valida a entrada e chama o predict.

Vale notar que o artefato carrega mais que o modelo. Como as variáveis são
percentis dentro do ano, ele guarda as distribuições de referência para
converter nota em percentil. Sem isso o app seria inutilizável, porque nenhum
educador sabe que o aluno está no percentil trinta e quatro de IPV.

### 29. O que acontece se alguém subir um arquivo com dados errados?

Existe validação em duas camadas. No arquivo: colunas obrigatórias, RA
duplicado, tipo numérico. Na linha: faixa dos indicadores, faixa de fase e
idade, e a diferença entre fase e fase ideal precisa estar dentro do intervalo
que existe na base histórica. Linhas fora da faixa são descartadas com aviso na
tela, nunca em silêncio, e a mensagem diz qual RA foi descartado.

### 30. A ferramenta pode induzir a equipe a estigmatizar alunos?

É um risco real e a gente tratou. Tem um aviso fixo no topo, visível nas três
abas, dizendo que o modelo mede descompasso de calendário e não dificuldade de
aprendizagem. E quando aparece o caso contraintuitivo, aluno defasado com risco
baixo, o app explica que é efeito de piso e que risco baixo significa
estabilidade, não ausência de necessidade de apoio.

A aba de documentação fecha dizendo que a decisão sobre cada aluno cabe à equipe
pedagógica. A ferramenta prioriza atendimento, não diagnostica.

---

## GitHub e reprodutibilidade

### 31. Por que os dados não estão no repositório?

Porque pertencem à Associação Passos Mágicos e foram cedidos para o datathon.
Repositório público com dado de menor, mesmo anonimizado, não se faz. O
gitignore bloqueia a planilha e o LICENSE separa explicitamente o código, que é
MIT, dos dados, que não são.

O artefato do modelo vai versionado porque tem só três vírgula oito kilobytes e
contém apenas estatísticas agregadas, nenhum registro individual.

### 32. Como alguém reproduz o trabalho?

Clona o repositório, instala o requirements, coloca a planilha em data barra raw
e roda os três notebooks na ordem. A semente está no config, não espalhada pelo
código. O carregador aceita qualquer nome de arquivo xlsx na pasta, porque o
nome original da banca tem espaços e downloads costumam trocar por underscore.

E tem uma camada a mais: os contratos de integridade quebram a execução se a
estrutura vier diferente do esperado. A gente testou cada contrato contra
corrupção injetada de propósito, e todos falharam como deveriam.

---

## Decisões de negócio

### 33. Se o modelo mede descompasso de calendário, para que serve?

Serve para duas coisas diferentes. No curto prazo, prioriza atendimento: entre
os trinta alunos que a coordenação consegue acompanhar, o modelo encontra onze
casos contra três da regra óbvia.

Mas a resposta mais valiosa é a outra. Descobrir que noventa e oito vírgula sete
por cento dos agravamentos vêm de dessincronia entre dois calendários muda a
pergunta da instituição. Em vez de perguntar quais alunos acompanhar, ela pode
perguntar por que as fases não acompanham o ano escolar. Isso é intervenção
estrutural e provavelmente vale mais que qualquer lista.

### 34. Qual é a primeira coisa que a Passos Mágicos deve fazer na segunda-feira?

Criar um alerta de evasão a partir da queda de engajamento. É a recomendação de
melhor retorno: o dado já é coletado, o custo é praticamente zero, e a evasão é
irreversível na prática, com só quatro retornos em três ciclos.

### 35. Falso negativo e falso positivo custam a mesma coisa aqui?

Não. Falso negativo é um aluno que precisava de acompanhamento e não recebeu.
Falso positivo é recurso gasto com quem não precisava tanto. Numa ONG com
capacidade limitada, os dois doem, mas o primeiro dói mais.

Por isso a métrica principal é recall entre os k primeiros, e não acurácia. A
pergunta que a coordenação faz não é "o modelo acerta?", é "atendendo os
cinquenta que eu consigo, quantos casos eu pego?".

---

## Se travar

Três frases que funcionam quando você não souber a resposta:

- "Não testamos isso e não vou chutar. É uma boa pergunta para a próxima
  iteração."
- "Essa limitação está declarada no relatório, e a razão é que os dados não
  permitem responder."
- "A gente errou isso na primeira versão e corrigiu na auditoria. Posso
  explicar o que mudou."

A terceira é a mais forte das três. Banca respeita quem encontra o próprio erro.
