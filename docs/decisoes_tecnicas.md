# Decisões técnicas

Registro do que foi decidido, das razões envolvidas e do que mudou ao longo do
desenvolvimento. O documento existe porque a pergunta mais frequente em uma
defesa é "por que vocês fizeram assim?", e a resposta precisa estar
documentada, não apenas lembrada.

---

## Decisões estruturais

### Painel em formato longo

Adotou-se uma linha por par de RA e ano, em vez de uma linha por aluno com
colunas sufixadas. Como o alvo é definido sobre transições, o formato longo
transforma essa operação em uma junção com deslocamento de ano, e não em
manipulação de nomes de coluna. A assimetria entre anos, como o IPP presente
apenas em 2023 e 2024 e o campo de ponto de virada apenas em 2022, converte-se
em valor nulo explícito. Além disso, a análise de coorte fechada, base da
auditoria de mudança de instrumento, torna-se direta.

### Separação temporal entre treino e teste

Foram identificados 468 alunos presentes nas duas janelas de transição. Uma
separação aleatória colocaria o mesmo aluno nos dois conjuntos. Optou-se por
treinar com as transições de 2022 para 2023 e testar com as de 2023 para 2024,
utilizando GroupKFold por RA no ajuste de hiperparâmetros.

O custo assumido é a perda do IPP, ausente em 2022, e um conjunto de treino com
600 linhas. A alternativa, empilhar as duas janelas com validação cruzada
agrupada, forneceria 1.365 linhas, porém sem validação em período futuro, que
constitui o núcleo da defesa metodológica.

### Percentil calculado dentro de cada ano

O IPS varia de 7,50 para 5,00 e retorna a 7,51 na coorte fechada, com
composição constante. Trata-se de mudança no método de cálculo, e não na
população. O percentil é imune a deslocamentos de escala.

O custo é a perda da informação de nível absoluto. A decisão se justifica
porque o uso pretendido é a priorização relativa, ou seja, a escolha de quem
atender dentro da coorte daquele ano.

Quanto à possível objeção de vazamento, o cálculo do percentil utiliza a
distribuição do ano inteiro, incluindo o conjunto de teste. Não configura
vazamento porque, em uso real, a coorte completa do ano está disponível antes
de qualquer previsão, e nenhuma informação sobre o alvo é transferida.

### Tratamento de zeros por indicador

| Indicador | Zeros | Decisão | Evidência |
|---|---|---|---|
| IAA | 249 | Convertido em nulo, com sinalizador | Lacuna de 0 até valores entre 1,7 e 3,5, sem persistência entre anos |
| IEG | 110 | Mantido | Lacuna menor e engajamento nulo é estado real |
| IDA | 23 | Mantido | Distribuição contínua com valores 0, 0,5, 0,7 e 0,9 |

A regra uniforme proposta inicialmente teria eliminado os 110 zeros do IEG, que
constituem informação legítima.

### Não utilização de SMOTE

Com 17,3% de eventos, a dificuldade não está na escassez de casos positivos,
mas na calibração. Exemplos sintéticos distorceriam justamente a probabilidade
que o enunciado exige que seja confiável.

### Escolha da regressão logística

Os intervalos de confiança dos cinco modelos se sobrepõem. Pelo critério
definido antes da execução, o empate leva ao modelo mais simples e mais bem
calibrado. A regressão logística também apresenta o melhor desempenho no
estrato de fase avançada, com 0,326 contra 0,262 do Random Forest, que é o
grupo no qual a previsão efetivamente importa.

---

## Revisões realizadas

### Hipótese de que o gradiente de fase seria artefato da régua: refutada

A régua mudou entre 2022 e 2023, quando ALFA passou de "2º e 3º ano" para
"1º e 2º ano", o que tornava a hipótese plausível. Entretanto, o padrão é
idêntico na janela em que a régua permaneceu estável, com taxas de 43,8% e
48,0% contra 10,2% e 8,4%. Trata-se de fenômeno real.

A ressalva sobre a régua permanece válida para comparações de nível absoluto
entre 2022 e 2023, mas não afeta o alvo.

### Hipótese de mudança generalizada de método nos indicadores: revisada

A afirmação inicial era ampla demais. Após a limpeza, verificou-se que apenas o
IPS apresenta variação severa e o IPV, moderada. A oscilação observada no IAA,
de 8,27 para 6,90 e depois para 8,54, decorria dos zeros de sentinela. Após sua
remoção, os valores passam a ser 8,67, 8,63 e 8,71.

A lição registrada é que um diagnóstico executado sobre dados não tratados
produz conclusão igualmente comprometida. A auditoria foi refeita após a
limpeza, e é esse resultado que prevalece.

### Hipótese de que a ausência de avaliação prediz piora: refutada

A hipótese foi sustentada durante quatro etapas do projeto e se mostrou falsa.
A taxa de piora é de 12,5% entre os alunos sem avaliação e de 17,7% entre os
avaliados, com p igual a 0,326 no teste de Fisher e sinal invertido em relação
ao esperado.

### IPP como principal recomendação: rebaixado

O IPP acrescentava 57% de R² sobre um modelo restrito, que continha apenas
defasagem e fase. Sobre o conjunto completo de variáveis, o ganho é nulo, com
PR-AUC passando de 0,634 para 0,635. A informação já estava contida no IPV e no
IDA.

### Restrição da população a defasagem menor ou igual a zero: retirada

A proposta visava eliminar a regressão à média entre alunos adiantados. A
decomposição mecânica demonstrou que o efeito de piso é pequeno quando
comparado ao efeito da fase ideal. A estratificação preserva mais dados do que
a exclusão.

### Variável de idade relativa à fase ideal: sem efeito

A variável foi apresentada como aquela que capturaria a mecânica do alvo, mas
obteve AUC univariada de 0,516. A dispersão de idade dentro de cada fase ideal
é ampla demais. Foi mantida no conjunto por ter custo baixo, porém sem o papel
previsto.

---

## Correções feitas na auditoria final

Antes da entrega, revisamos o projeto do ponto de vista de um avaliador
externo. Quatro afirmações precisaram ser reescritas.

### Limites de Manski aplicados de forma incorreta

A versão anterior afirmava que, assumindo que todos os alunos que saíram
tivessem piorado, a melhora entre ciclos permanecia em 9,4 pontos. O cálculo
subtraía o limite inferior de uma janela do limite inferior da outra, o que não
é um limite válido para uma diferença.

O limite correto usa o melhor caso da primeira janela contra o pior caso da
segunda, resultando em um intervalo de -20,9 a +33,9 pontos, que contém zero.
Em outras palavras, os dados sozinhos não provam que o segundo ciclo foi
melhor.

O que continua válido é a melhora dentro da coorte fechada, com Wilcoxon
p = 7,5e-35, e a comparação entre ciclos condicionada a uma atrição parecida
nos dois anos, de 30,2% e 24,6%.

### Escolha do modelo apresentada como liderança

O texto dizia que a regressão logística liderava no estrato de fase avançada.
A diferença para o Random Forest é de +0,057, com IC 95% de -0,043 a +0,157 e
p = 0,25. Os modelos empatam. A escolha continua legítima pelo critério de
parcimônia e calibração definido antes da comparação, mas não por desempenho
superior.

### Ganho de desempenho expresso como múltiplo

O relatório afirmava que o modelo captura 3,7 vezes mais casos que a regra
simples. Isso vem de 11 acertos contra 3, entre 50 eventos. Com contagens tão
pequenas, o múltiplo é instável, e passamos a reportar os números absolutos.

### Circularidade possível no IPV

O IPV aparece como principal fator de proteção, com razão de chances de 0,46.
Verificamos que ele é também o melhor preditor isolado da promoção de fase,
com AUC de 0,679, que é justamente a decisão que gera o alvo. Se a coordenação
consulta o IPV ao decidir promoções, parte da previsão é circular. Não há como
verificar com os dados disponíveis, e passou a constar como limitação.

### Achado de evasão sem modelagem

A conclusão sobre engajamento e evasão vem de teste univariado, sem controle
por fase, idade ou tempo de programa, e sem excluir as fases terminais, nas
quais sair pode significar concluir o programa. O texto passou a tratar o
resultado como associação e não como capacidade preditiva.

---

## Erros encontrados e corrigidos

| Erro | Como foi detectado | Correção |
|---|---|---|
| Separador de milhar removendo casa decimal | INDE com valor máximo de 8337 e média de 15,3 | Remoção condicionada à presença de vírgula decimal |
| Tamanho de turma sem agrupamento por fase | Estatística KS de 0,894 entre treino e teste | Agrupamento por ano, fase e turma |
| Uso de `class_weight='balanced'` | Índice de Brier de 0,179, pior que a regra simples | Parâmetro removido, pois compromete a calibração |
| Indicador de ausência de avaliação não detectava 2024 | Zero casos identificados onde havia 102 | Critério por contagem, em vez de verificação total |
| Bloco de fase usando a fase cursada | Não reproduzia o padrão observado | Substituição pela fase ideal |
| Notebooks sem quebra de linha nas células | Jupyter concatenava todo o conteúdo | Inclusão de quebra ao final de cada linha |

O primeiro e o terceiro casos só foram identificados porque a validação
examinou a distribuição dos valores, e não apenas o esquema. Nenhum deles seria
detectado por inspeção visual.

---

## Lacunas não resolvidas

- O ano escolar do aluno não consta na base, o que impede testar se o risco
  decorre do descompasso entre a progressão escolar, automática, e a promoção
  de fase, pedagógica. Essa era a hipótese de maior valor gerencial do projeto.
- O motivo da saída não é registrado, o que impede distinguir abandono de
  mudança de cidade ou de conclusão do programa.
- A rubrica oficial de avaliação do datathon não estava disponível, de modo que
  os critérios de sucesso foram inferidos a partir do enunciado.
- Os pesos do INDE não constavam no dicionário e foram recuperados por
  regressão, com R² igual a 1,000000: 0,20 para IEG, IDA e IPV, e 0,10 para
  IAA, IPS, IPP e IAN.
