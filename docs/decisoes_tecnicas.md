# Decisões técnicas

Registro do que foi decidido, por quê, e o que mudou de ideia no caminho.
Existe porque em datathon a pergunta mais cara na defesa é "por que vocês
fizeram assim?" — e a resposta precisa estar escrita, não lembrada.

---

## Decisões estruturais

### Painel longo, não wide
Uma linha por `(ra, ano)` em vez de uma linha por aluno com colunas sufixadas.
O alvo é definido sobre transições, e no formato longo isso é um `merge` com
deslocamento de ano em vez de manipulação de nomes de coluna. A assimetria
entre anos (IPP só em 23–24, `Atingiu PV` só em 2022) vira `NaN` explícito, e
análise de coorte fechada — coração da auditoria de drift — fica trivial.

### Split temporal, nunca aleatório
468 alunos aparecem nas duas janelas. Split aleatório colocaria o mesmo aluno
dos dois lados. Treino em 22→23, teste *out-of-time* em 23→24, `GroupKFold`
por `RA` no tuning.

Custo assumido: perde-se o IPP (não existe em 2022) e o treino fica com 600
linhas. A alternativa — empilhar as janelas com CV agrupada — daria 1.365 mas
sem validação *out-of-time*, que é o núcleo da defesa metodológica.

### Percentil intra-ano
O IPS oscila 7,50 → 5,00 → 7,51 na coorte fechada, com composição constante.
Mudança de método de cálculo, não de população. Percentil é imune a
deslocamento de escala.

Custo: destrói informação de nível absoluto. Aceito porque o uso é priorização
*relativa* — a ONG escolhe a quem atender dentro da coorte daquele ano.

Sobre a objeção de vazamento: calcular percentil usa a distribuição do ano
inteiro, incluindo o conjunto de teste. Não é vazamento porque, em produção,
a coorte inteira do ano está disponível antes de qualquer predição. Nenhuma
informação sobre o *alvo* atravessa.

### Zeros tratados por indicador
| Indicador | Zeros | Decisão | Evidência |
|---|---|---|---|
| IAA | 249 | → `NaN` + flag | Gap de 0 até 1,7–3,5; não-persistente entre anos |
| IEG | 110 | manter | Gap menor; engajamento nulo é estado real |
| IDA | 23 | manter | Continuum 0 / 0,5 / 0,7 / 0,9 |

A regra uniforme proposta inicialmente teria destruído os 110 zeros de IEG,
que são informação legítima.

### Sem SMOTE
A 17,3% o problema não é escassez de positivos, é calibração. Positivos
sintéticos distorcem exatamente a probabilidade que o briefing pede que seja
confiável.

### Regressão logística sobre boosting
Empate dentro do IC entre os cinco modelos. Pela regra declarada **antes** de
rodar, empate leva ao mais simples e mais calibrado. A logística também vence
no estrato de fase avançada (0,326 vs 0,262 do RF), que é onde a predição
importa.

---

## Revisões — o que mudou de ideia

### O gradiente de fase seria artefato da régua (H3) — REFUTADO
A régua mudou entre 2022 e 2023 (`ALFA` de "2º e 3º ano" para "1º e 2º ano"),
então a hipótese era plausível. Mas o padrão é idêntico na janela onde a régua
ficou estável (43,8% e 48,0% contra 10,2% e 8,4%). Fenômeno real.

A ressalva sobre a régua **permanece válida** para comparação de nível absoluto
entre 2022 e 2023 — só não contamina o alvo.

### "Os indicadores mudaram de método" (H10) — REVISADO
Afirmação ampla demais. Após limpeza, só o **IPS** tem drift severo e o **IPV**
moderado. A oscilação do IAA (8,27 → 6,90 → 8,54) era artefato dos zeros
sentinela — removidos, fica 8,67 / 8,63 / 8,71.

Lição registrada: diagnóstico rodado sobre dado sujo produz conclusão suja. A
auditoria de drift foi refeita **após** a limpeza, e é esse resultado que vale.

### Ausência de avaliação prediz piora (H17) — REFUTADO
Hipótese sustentada por quatro etapas do projeto. Falsa: 12,5% de piora entre
os sem avaliação contra 17,7% entre os avaliados, Fisher p = 0,326 — e com o
sinal **invertido**.

### IPP como recomendação nº 1 — REBAIXADO
O IPP agregava +57% de R² sobre um modelo pobre (só defasagem + fase). Sobre o
conjunto completo de features, o ganho é **nulo** (PR-AUC 0,634 → 0,635). A
informação já estava contida no IPV e no IDA.

### Restringir população a `Defas_t ≤ 0` — RETIRADO
Proposto para eliminar regressão à média entre alunos adiantados. A decomposição
mecânica mostrou que o efeito de piso é pequeno perto do efeito de fase ideal.
Estratificar preserva mais dado que excluir.

### `idade_rel_fase_ideal` — FALHOU
Apresentada como "a feature que captura a mecânica do alvo". AUC univariado de
0,516. A dispersão de idade dentro de cada fase ideal é grande demais.
Mantida no conjunto por ser barata, mas sem o papel previsto.

---

## Bugs encontrados e corrigidos

| Bug | Como apareceu | Correção |
|---|---|---|
| Separador de milhar comia decimal | `INDE` máximo de 8337 (média 15,3) | Só remove ponto quando há vírgula na string |
| `tamanho_turma` sem agrupar por fase | KS de 0,894 entre treino e teste | `groupby(ano, fase, turma)` |
| `class_weight='balanced'` | Brier 0,179, pior que o baseline | Removido — destrói calibração |
| `sem_avaliacao` não detectava 2024 | 0 casos onde havia 102 | Critério por contagem, não `.all()` |
| `bloco_fase` usava fase cursada | Não reproduzia o achado | Trocado para `fase_ideal_num` |
| Notebooks sem `\n` nas linhas | Jupyter concatenava tudo | `\n` terminal em cada linha |

O primeiro e o terceiro só apareceram porque a validação olhou **distribuição**,
não schema. Nenhum seria pego por inspeção visual.

---

## Lacunas não resolvidas

- **Ano escolar do aluno** não existe na base. Impede testar se o risco vem do
  descompasso entre progressão escolar (automática) e promoção de fase
  (pedagógica) — a hipótese de maior valor gerencial do projeto.
- **Motivo da saída** não registrado. Não distinguimos abandono de mudança de
  cidade ou conclusão.
- **Rubrica oficial de avaliação** do datathon não disponível; critérios de
  sucesso foram inferidos do enunciado.
- **Pesos do INDE** não estavam no dicionário — recuperados por regressão
  (R² = 1,000000): 0,20 para IEG/IDA/IPV, 0,10 para IAA/IPS/IPP/IAN.
