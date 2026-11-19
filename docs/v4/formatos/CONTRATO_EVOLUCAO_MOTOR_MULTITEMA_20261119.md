# Contrato técnico de evolução do motor documental — multitema
**19/11/2026 · Branch experimental `atlas-direcao-visual-20261118`**

## Decisão do responsável
Cada correção deve melhorar o **motor** e beneficiar futuros assuntos, e não depender de Taiwan, Canal do Panamá, Venezuela ou Suez. Episódios específicos são casos de teste, nunca motor paralelo. Não aceitar "93 testes verdes" como aprovação estética de filme, ou transformar recortes aleatórios em prova factual.

## Reusar antes de criar
| Necessidade | Dono existente | Não duplicar |
|---|---|---|
| Plano audiovisual por acontecimento | `src/v3/plano_av.py` e `src/v4/formatos/direcao_eventos.py` | Outro diretor temático |
| Contrato comum de qualidade visual | `src/v4/formatos/contrato_visual_comum.py` | Fiscal novo para cada episódio |
| Portão de mídia/ação antes de gastar IA | `src/v4/formatos/gate_filme_completo.py` | Gate Taiwan/Suez/Venezuela separado |
| Cartografia com procedência | `src/v4/formatos/ponte_mapa_atlas.py` | Recriar mapa no montador |
| Biblioteca global (SQLite + bytes SHA) | `src/v3/biblioteca.py`, `src/v4/formatos/ponte_biblioteca.py` | Banco paralelo de mídia |
| Montagem e fontes | `src/v4/formatos/filme_editorial.py` | Segundo montador ATLAS |
| Narração natural e plataforma | `src/v4/formatos/tempo_natural.py` + `plataformas.json` | Fixar 25–30 ou 60–90s no prompt de tema |

## Invariantes de produção
1. **Intenção → fato → mídia → comportamento visual → consequência.** O mesmo contrato integral (`cenas[*].acao/promessa/midia`) já é obrigatório para filmes finais. Não pedir de novo os mesmos campos sob outro nome nos shots: respeitar a verificação de correspondência 1:1 já existente.
2. **Cena incompleta não vira aprovação técnica.** O portão agora devolve `cobertura_acontecimentos`, com `id`, intenção, tipo visual, bloqueios locais e status técnico. Status `SEM_BLOQUEIO_LOCAL_REVISAO_HUMANA_PENDENTE` NÃO equivale a aprovação visual ou editorial; bloqueios globais ficam separados.
3. **Duração narrativa por padrão em novos contratos.** Se `politica_duracao.modo` não foi explicitamente escolhido e `janela_duracao_s` não existe, o portão usa `narrativa`, sem teto global. Janelas antigas continuam nos fixtures que as declararam. Os limites individuais de cena, progressão e integridade não são abolidos.
4. **Plataformas são avaliação de distribuição, não geradoras de duração.** TikTok Creator Rewards: >60 s, 65 s apenas preferência; YouTube Shorts até 180 s; quando o master não cabe, não amputar nem preencher com cenas vazias.
5. **Representação é permitida; falsa identidade não.** Laboratório NIST pode explicar manuseio de wafer, não virar cena gravada na TSMC nem trocar e-beam por EUV. Inspeção real de quadros, direitos, fonte original e SHA são obrigatórios.
6. **Regressões devem ser multitema:** no mínimo uma situação geográfica, uma de ação/mecanismo, uma com registro/procedência e uma de indústria/efeito. O novo `tests/test_gate_multitema_cobertura.py` cobre Venezuela/relevo, Suez/ação, mapa de conflito sem comprovação, chips/efeito e mídia repetida. Testes de dados fictícios sempre explicitam `conferir_bytes=False` (jamais no CLI real).
7. **Monitorar generalização:** o workflow `.github/workflows/qa-filme-taiwan-portao.yml` (nome agora multitema) roda em alterações do motor Python, da avaliação de plataforma e das regressões. O piloto Taiwan permanece dentro dele como **regressão deliberadamente bloqueada**, não como único tema possível.
8. **Aprovação humana separada:** nenhum número de testes, metadados, classificação visual ou pixel motion equivale à validação estética da prévia final. Não enviar Telegram, publicar ou chamar Gemini Charon quando o portão estiver bloqueado.

## Estado após implementação
- Novo modo default `narrativa` para contratos sem janela, relatórios locais por evento no portão existente;
- Testes adicionais multitema sem chamadas IA, render ou publicação;
- CI **44613185916**, 98 testes aprovados, mapa ATLAS Taiwan autenticado e 11 pendências mantidas;
- Integração de workflow reativa a mudanças do motor, não apenas alteração de um arquivo de disparo;
- Não altera `main`, NTC nem DOSSIÊ.

## Próximo critério de aceite (visual e editorial)
1. Reidratar fontes, demonstrar ação real com direito de uso confirmado, sem atribuir identidade falsa;
2. Vincular fatos a cada acontecimento e preencher lacunas sem fabricar segundos;
3. Fazer o roteiro completo de um tema **e rodar exatamente o mesmo diagnóstico em outro tipo de história**, sem nenhuma condição `if tema == "taiwan"`;
4. Só então permitir geração de Charon, MP4 privado e aprovação humana. CI verde significa código funcionando, não vídeo bonito.

**O usuário não autorizou mover essa branch para `main`.**
