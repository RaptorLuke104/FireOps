# FireOps — Punte animate v0.9

Richiede **Unico-v08 con la correzione della fiamma che non si stacca**, già funzionante. Il bridge v2 e il client Unico-v08 restano invariati.

## Cosa cambia

Il movimento non viene più affidato alla sola larghezza del quad. Una nuova texture contiene **16 fotogrammi** in una striscia orizzontale 16×1: le punte si incurvano lateralmente e cambiano leggermente altezza, mentre la parte bassa della texture rimane identica in tutti i fotogrammi.

- Texture atlas **4096×256**, 16 fotogrammi da 256×256. È una sola texture, NON 16 effetti XML.
- La deformazione è nulla nel 30% inferiore della texture e aumenta gradualmente verso le punte.
- Tre cicli dell'animazione durante la vita di ogni particella, circa 7,5–12,6 fotogrammi/s con le vite attuali; fase iniziale diversa fra particelle per non sincronizzare tutte le lingue.
- Disabilitata la precedente pulsazione della larghezza dell'intera sagoma. Scala geometrica e posizione non oscillano durante la vita della particella.
- Velocità delle particelle di fuoco ancora zero: la fiamma non viene lanciata verso l'alto.
- Invariati fumo, numero/rate delle particelle, vite, curve alpha e capacità totale di **256**.
- Rimane **un solo VisualEffect**: stesso GUID, stesso file di libreria, stessi sei GraphParameter e protocollo v2.

Il nuovo materiale è **FireOps_Flame_Tips_v09**. Mantiene shader, blend, opacità ed emissivo del materiale precedente; cambia soltanto la texture assegnata e l'identità del materiale. Il materiale del fumo non viene modificato.

La tecnica è un'animazione di sprite deformati, non una simulazione fluidodinamica. Deve ancora essere verificata nel renderer di MSFS. La texture ha circa un milione di pixel, contro circa 262 mila della vecchia 512×512: il numero di particelle non aumenta, ma il costo di memoria della texture cresce. La risoluzione del singolo fotogramma è 256×256.

`Anteprima-punte.gif` mostra **solo la texture animata fuori dal simulatore**, non è un render MSFS e non dimostra la corretta riproduzione dell'atlas nel gioco.

## Questa volta non basta scaricare solo l'XML

Servono tre file installati insieme:

1. `FireOps_Unified_v08.xml` aggiornato;
2. `FireOps_Flame_Tips_v09.material` nuovo;
3. `Textures/fireops_flame_tips_v09.png` nuova.

L'installer li copia e crea un backup. Non modifica il WASM, il client, la libreria VFX o i vecchi materiali. Non creare un nuovo progetto.

## Installazione

1. Nel client attuale esegui `clear`, poi `quit`.
2. **Chiudi MSFS**, per evitare ricaricamenti mentre vengono aggiunti texture e materiale.
3. Estrai lo ZIP in **C:\FireOps\Punte-v09**, separato da Unico-v08.
4. Esegui **INSTALLA-PUNTE.cmd**. Il progetto predefinito resta **C:\FireOps\SimpleFX**. Se appare STOP, invia il messaggio e non procedere.
5. Riapri MSFS e il progetto **SimpleFX.xml**. Esegui **Build All solo su SimpleFX**. Non ricompilare il bridge e non rieseguire INSTALLA-UNICO.
6. Se la build segnala un errore, invia **il primo errore completo** prima di usare Load In Editor. I test locali non sostituiscono il compilatore SDK.
7. Dopo una build riuscita, apri la libreria con **Load In Editor**.
8. Il nome dell'effetto nel grafo è **FireOps_Unified_v09**, ma il file resta **FireOps_Unified_v08.xml** per mantenere invariati il riferimento di libreria e il GUID richiesto dal bridge. È intenzionale.
9. Nel Material Inspector del nuovo **FireOps_Flame_Tips_v09**, esegui **Load**, come nei precedenti collaudi. Non caricare solo il vecchio FireOps_Flame_v02.
10. Gli Output della fiamma devono mostrare **Material = FireOps_Flame_Tips_v09**, **UVMode = Atlas**, **AtlasSize = 16, 1**. Il fumo resta col materiale Dense_v06 e UVMode Default.

## Prova

Avvia sempre lo stesso client:

```text
C:\FireOps\Unico-v08\TestLocale\AVVIA.cmd
```

Attendi ACK v2 e, con aereo fermo a terra:

```text
effects fire
size base
world auto
```

Aspetta 8–10 secondi perché le fiamme si sovrappongano, poi osserva per almeno 20 secondi. L'ACK atteso è live 1, failed 0. La base deve rimanere sul posto e il movimento deve concentrarsi sulle punte, senza far salire l'intera sagoma.

Un breve video di 10–15 secondi è più utile di uno screenshot per questo controllo. Se vedi una fila di molte fiamme nello stesso quad, oppure una texture ferma, controlla materiale, UVMode e AtlasSize prima di cambiare altre impostazioni.

Dopo la prova isolata puoi tornare a `effects both` / `world auto`. Il fumo è stato verificato strutturalmente invariato nei test offline.

## Backup e ripristino

Il backup è accanto a SimpleFX, **C:\FireOps\FireOps-backup-punte-v09-...**; il percorso esatto è in `RISULTATO-INSTALLAZIONE.txt`. Conservalo senza spostarlo. Nessun backup precedente viene eliminato.

Con client e MSFS chiusi, dalla cartella Punte-v09:

```powershell
py -3 install_tips.py --project "C:\FireOps\SimpleFX" --restore "C:\FireOps\FireOps-backup-punte-v09-..."
```

Sostituisci il percorso completo. Il ripristino recupera l'XML precedente e rimuove gli asset aggiunti se prima assenti; rifiuta file modificati dopo la patch. Poi esegui Build All su SimpleFX e ricarica il materiale precedente. Il client e il bridge rimangono sempre quelli di Unico-v08.

Verifica preliminare senza modifiche (a MSFS chiuso):

```powershell
py -3 install_tips.py --project "C:\FireOps\SimpleFX" --check
```

## Note di implementazione e verifiche

L'indice del fotogramma è generato dall'età normalizzata tramite una curva scalare e una fase casuale per particella; è collegato a ParticleTextureIndex nell'Update. L'Output usa Atlas con 16 celle orizzontali. Non viene introdotto un timer nel WASM o una nuova variante di effetto per fotogramma.

La documentazione SDK della proprietà ParticleTextureIndex contiene un esempio incongruente copiato dal colore; qui è utilizzato l'ingresso scalare FloatIn coerente con l'indice texture descritto dall'editor. **Questa sintassi e il comportamento dell'atlas richiedono ancora conferma dal compilatore e dal renderer SDK dell'utente.** Non è stato eseguito un collaudo Windows/MSFS.

Fonti tecniche consultate:
- https://docs.flightsimulator.com/html/Developer_Mode/VFX_Editor/Nodes/AtlasPlayer.htm
- https://docs.flightsimulator.com/msfs2024/retail/content-configuration/visualeffects/visual-effects-xml-properties/
- https://docs.flightsimulator.com/msfs2024/retail/content-configuration/visualeffects/visual-effects-shared-xml-elements/

Otto test locali: dimensioni atlas; base identica fra fotogrammi e punte differenti; un solo effetto/capacità 256; collegamenti e GUID; velocità zero della fiamma; fumo invariato; manifest/materiale; installazione/ripristino e protezione delle modifiche. Esito in TEST_RESULTS.txt.

Il generatore in `tools/create_patch.py` richiede Pillow e NumPy soltanto per rigenerare le immagini offline. L'installazione usa i tre asset già pronti e solo Python standard. `tests/fixture` non è un progetto da aprire nel simulatore.
