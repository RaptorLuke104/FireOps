# Materiali VFX
`flame.png` e `smoke.png` sono sprite RGBA procedurali originali per il prototipo, non fotografie e non flipbook animati.
Importali nel Material Editor SDK in una MaterialLib dedicata. Parti dal materiale VFX funzionante di SimpleFX per conservare shader/blending appropriati; duplica il materiale dall'editor con un GUID nuovo, non copiare un GUID esistente.
Per la fiamma usa alpha blending/emissione adatta al materiale VFX; per il fumo alpha blending e niente emissione. Evita materiali opachi: apparirebbero rettangoli.
`tools/make_vfx.py` richiede i due GUID REALI dei materiali che hai creato. Genera grafi XML base con GUID degli effetti distinti dai GUID materiali. Aprili e validali nell'editor prima di compilare. Sono un effetto dimostrativo semplice, non un incendio fotorealistico.
