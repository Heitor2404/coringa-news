"""Soft retrieval routing by declared provider coverage, not a topic template."""
from src.v4.formatos.revisao_documental import termos_consulta,relevancia_textual,incompatibilidade_metadados
# Provider capabilities, not a closed list of permitted subjects. Every route
# remains eligible; no domain match falls back to the historical order.
CAPABILITIES={
    'usgs_pagina':{'volcano','volcanic','lava','earthquake','geology','landslide','glacier','geological','erosion'},
    'noaa_pagina':{'ocean','oceanic','submarine','underwater','deepsea','marine','octopus','coral','seafloor','hydrothermal'},
    'nasa_video':{'spacecraft','space','astronaut','orbit','lunar','mars','satellite','rocket','spaceflight'},
    'nasa':{'spacecraft','space','astronaut','orbit','lunar','mars','satellite','rocket','spaceflight'},
    'inaturalist':{'wildlife','species','bird','hummingbird','insect','plant','butterfly','amphibian','reptile'},
    'nist_pagina':{'antenna','measurement','metrology','laboratory','materials','engineering','robot','calibration'},
    'smithsonian':{'museum','artifact','historical','aviation','locomotive','archive','specimen'},
    'archive_video':{'historical','archival','archive','silent','newsreel','vintage'},
    'figshare':{'microscopy','experiment','scientific','laboratory','microscope','cell','dataset'},
}
def sinais(need,query):
    p=need.get('pesquisa') or {}
    return set(termos_consulta(' '.join([str(query),str(need.get('sujeito') or ''),*(str(x) for x in p.get('contexto_busca') or [])])))
def afinidade(need,query,provider):
    return len(sinais(need,query)&CAPABILITIES.get(provider,set()))
def candidato_promissor(need,c):
    # Text is a signal for scheduling, never a gate or a proof of coverage.
    score=relevancia_textual(need,c)
    return (score['cobertura']>=.6 and score['titulo']>=.25 and
            not incompatibilidade_metadados(need,c) and c.get('natureza_preliminar')!='REPRESENTACAO_DECLARADA')
