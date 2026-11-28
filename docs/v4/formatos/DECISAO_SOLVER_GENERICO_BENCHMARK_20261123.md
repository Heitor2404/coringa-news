# Decisão de arquitetura após auditoria independente — 23/11/2026

**Estado:** benchmark congelado, decisão de substituir gradualmente o núcleo por composição genérica AINDA SUJEITA A PROVA. Nenhuma alteração em motores existentes ou produção.

## Diagnóstico verificado no código

A auditoria externa sugeriu parar a expansão linear F7–F17 por família. A inspeção no GitHub confirma: `compilador_topologia_f15.py` tem dois registros escritos manualmente, `relacoes_com_evidencia_f17.py` tem um pequeno conjunto de regex e formatos fixos, `cinematica_biela_manivela.py` impõe coordenadas 540×960, `compositor_engrenagens_f14.py` usa grandes trechos SVG monolíticos; `biblioteca_componentes_fisicos.py` é um registro fechado por validação. A regressão e procedência são úteis, mas não comprovam generalização. Nenhuma família nova foi comprovadamente criada por composição genérica.

**Decisão:** não construir F18 como renderer específico de tesoura antes de uma experiência de solver comum. Reaproveitar F7 (oráculo cinemático), F14 (teste de relação dentada), F16/F17 (fontes e bloqueios), primitives de desenho e QA de UI, com implementação gradual e reversível em subdiretório isolado. Não apagar o que já existe nem promover antes de evidência.

## Benchmark congelado

`benchmarks/generalizacao_mecanismos_v1.json`: lista de **12 mecanismos inéditos** com fontes técnicas para PRINCÍPIOS, critérios de movimento, quatro casos holdout e escala de resultados 0–4.

**O benchmark NÃO foi executado ainda.** Não chamar ausência de implementação de prova empírica de zero desempenho, nem alegar `8/12` como factível. Não editar essa lista durante os experimentos para facilitar a pontuação. Registrar `manual_spec`, `source_generated_spec`, acurácia física, avaliação estética, intervenção humana e custo *separadamente*.

**Critério de acerto real:** no mínimo nível 3 — trajetória cinemática correta e renderizada por um solver e renderer **compartilhados**, sem lógica exclusiva para o nome do mecanismo. Vídeo genérico ou animação pré-gravada não contam. Nível 4 exige julgamento visual independente e comparação com fonte confiável.

## Correções à proposta da auditoria

1. **Um solver não resolve tudo magicamente.** Cames, correntes, catracas, cruz de Malta e coroa-sem-fim exigem contato, geometria espacial ou condições unilaterais que pivô/prismática/engrenagem não cobrem automaticamente. O conjunto planetário pode ter **dois graus de liberdade** sem uma terceira condição (ex.: anel fixo), logo exigir DOF=1 universalmente é erro.
2. **Pymunk é candidato de protótipo, não escolhido de antemão como solver de cinemática exata.** Documenta PivotJoint/GrooveJoint/GearJoint e licença MIT; é orientado a física dinâmica e pode introduzir erro de aproximação/deriva. Comparar com resolução geométrica de restrições, especialmente fechamento de quatro barras e Scotch yoke. **MuJoCo Apache 2.0** é alternativa para 3D/complexidade; **SolveSpace GPLv3** pede revisão de licença antes de eventual incorporação.
3. O renderer deve consumir **poses e corpos em unidades do modelo**, convertendo para pixels **apenas na câmera**. O motor4 já fixa `remotion`, `@remotion/three` e `three` no package.json, mas isso não prova uma pipeline 3D integrada e calibrada. Rever condições da licença Remotion na distribuição.
4. Não confundir **kinematics** com hidráulica de força. Para demonstrar a tesoura movida por atuador basta cinemática do atuador e pivôs; valores reais de pressão e segurança só para alegações sobre engenharia/hidráulica de máquina específica.
5. Custos de LLM por modelo e meta de `8/12` são hipóteses a medir. Primeiro executar benchmark baseline do compilador atual e testar 2–3 topologias com composição genérica.

## Execução recomendada

- **E0 (já iniciada):** lista de 12, fontes, critérios e holdouts congelados. FALTA medir linha de base: tentar gerar trajetórias pelos sistemas existentes sem alterar código, guardar status/recusas e evidências.
- **E1 (spike):** definir `MechanismSpec` contendo `bodies`, `joints`, `ground`, `driver`, `units`, `evidence`; prototipar solver 2D no laboratório e comparar quantitativamente F7, quatro barras e Scotch yoke. Testes: fechamento em coordenadas do mecanismo, continuação de solução ao longo do ciclo, ausência de saltos/singularidades injustificadas, determinismo por tempo e movimento articulado correto. Priorizar limites e não encolher objetos.
- **E2 (renderer genérico):** corpos visuais (barra, disco, pistão, engrenagem) apresentados por um renderer comum, recebendo poses do solver e separando layout/editorial. Depois piloto 3D com `@remotion/three` reaproveitando o MESMO `MechanismSpec` e trilha de poses.
- **E3 (ingestão):** LLM gera `MechanismSpec` proposto com citação por junta e incerteza, validador mecânico rejeita o impossível, custo real e taxa de acerto medidos contra benchmark holdout; a aprovação visual segue humana.

**Segurança de produção:** branch `atlas-direcao-visual-20261118` apenas; `main`, NTC, DOSSIÊ, Telegram, publicação e motores atuais NÃO alterados.

**Fontes de software (confirmadas na documentação pública 23/11/2026):** Pymunk https://www.pymunk.org/en/latest/pymunk.constraints.html e licença MIT https://www.pymunk.org/en/latest/ ; MuJoCo https://github.com/google-deepmind/mujoco (Apache-2.0); SolveSpace https://solvespace.github.io/solvespace-web/library.html (GPLv3); Remotion https://www.remotion.dev/docs/three e licença https://www.remotion.dev/docs/license/pricing .
