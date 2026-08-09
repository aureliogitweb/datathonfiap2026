# Pendências

Estado após o Passo 13. Só resta execução.

---

## Obrigatório

### 1. Gravar o vídeo
Roteiro pronto em `roteiro_video.md`, 642 palavras, 4min35s em ritmo normal.
Grave em blocos, um slide por vez, e junte na edição.

### 2. Publicar no Streamlit Community Cloud
O app está pronto e testado localmente. Instruções em `app/README.md`.
Depois de publicar, cole a URL no `README.md`, no marcador da seção inicial.

### 3. Rodar os notebooks e salvar com as saídas
Se algum notebook subir sem output, a banca abre e não vê resultado.
Confira no GitHub antes de considerar entregue.

### 4. Corrigir o notebook 02 à mão
Na seção da Pergunta 10 há uma célula markdown que ainda afirma que a melhora
resiste ao pior caso com 9,4 pontos. O texto substituto está no final deste
arquivo.

---

## Opcional, se sobrar tempo

### Modelo secundário de evasão
É o maior ganho marginal disponível. O sinal é mais forte que o do alvo
principal (IEG com p = 7e-14 contra AUC 0,523 para defasagem), o problema é
maior (25% a 30% saem por ano) e a saída é irreversível (só 4 retornos em três
ciclos). Usa dados que já existem.

Implementação: alvo igual a ausência no ano seguinte, mesmo pipeline, mesma
separação temporal, excluindo as fases terminais porque na Fase 8 sair pode
significar concluir.

---

## Encerrado, não insistir

| Item | Motivo |
|---|---|
| Ano escolar do aluno | Não existe na base, confirmado |
| Rubrica oficial de avaliação | Não disponível |
| Análise SHAP | Modelo linear, coeficientes já bastam |
| IPP como recomendação | Ganho nulo sobre o conjunto completo |

---

## Texto substituto para o notebook 02, Pergunta 10

> **Resposta.** A melhora dentro da coorte é inequívoca: 58,8% melhoraram
> contra 10,3% que pioraram, com Wilcoxon p = 7,5e-35. Já a comparação entre
> ciclos é mais frágil do que parece. Os limites de Manski por janela são
> [21,5%; 51,7%] e [30,9%; 55,4%], e como se sobrepõem, os dados sozinhos não
> provam que o segundo ciclo foi melhor. O que sustenta a comparação é a
> atrição parecida nos dois anos, 30,2% e 24,6%, o que é suposição e não
> garantia.

---

## Estrutura final dos entregáveis

| Entregável do enunciado | Situação |
|---|---|
| Link do GitHub com os códigos | Pronto |
| Apresentação de storytelling | Pronto, 10 slides mais 3 anexos |
| Notebook com o modelo preditivo | Pronto, falta salvar as saídas |
| Aplicação no Streamlit com deploy | Pronto, falta publicar |
| Vídeo de até 5 minutos | Falta gravar |
