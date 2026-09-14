# FireOps — Unico v0.8 / recupero dopo crash nell'editor

## Cosa viene consegnato

Il solo grafo FireOps attivo diventa **FireOps_Unified_v08.xml**, nella radice di questo kit. Contiene **un VisualEffect con quattro emettitori** (tre fiamme, uno fumo), non 60 varianti né molti effetti racchiusi nello stesso file.

Il crash segnalato è avvenuto aprendo la libreria/editor v0.7. Non è disponibile un crash log: non è dimostrato che la causa fosse il numero di grafi. Questa revisione elimina comunque il catalogo e limita il costo della prova. Non è una garanzia contro ogni crash del simulatore.

### Cambiamenti strutturali

- 60 grafi random v0.7 rimossi dai sorgenti attivi e dai riferimenti di libreria; originali conservati in backup esterno.
- Anche FireOps_Flame.xml / FireOps_Smoke.xml e i loro sidecar noti vengono archiviati: nel progetto resta **un solo grafo FireOps**. EngineSmoke e gli eventuali effetti di terzi non vengono rimossi.
- Un solo file VFX con 91 nodi, quattro emettitori e **256 particelle di capacità complessiva massima**: 32 + 32 + 32 + 160.
- Emissione fiamme 8/6/6 al secondo, fumo 5 al secondo. Vita fumo 18–28 secondi invariata; a regime il massimo nominale è 140 particelle di fumo, non circa mille.
- Raggio superiore del fumo ridotto da 32 m della v0.6 a 12 m prima del fattore di larghezza; limite effettivo 15,6 m con il fattore massimo 1,3. Limitare la sovrapposizione di grandi quad è importante oltre al numero di file.
- Materiali/texture già caricati e approvati conservati: **FireOps_Flame_v02** e **FireOps_Smoke_Dense_v06**. Non vengono toccati, compreso l'emissivo della fiamma.
- **Un incendio alla volta**: limite verificato nel bridge, non solo nel client.

La densità e la forma possono differire dalla base approvata perché sono state ridotte emissione e dimensioni del fumo per una prova più conservativa. Non promettiamo identica resa a un quarto del carico; il compromesso va valutato in simulatore.

## Randomizzazione con un solo XML

Il grafo contiene sei GraphParameter: **FireScale, SmokeWidth, SmokeRise, SmokeDensity, FireOn, SmokeOn**. Il bridge li passa al momento dello spawn usando `FsVfxGraphParam` e la API a **sei argomenti** già disponibile nel tuo SDK. Nessuna dichiarazione inventata o settimo argomento.

La scelta viene derivata dall'ID della generazione e resta stabile; non cambia a ogni heartbeat. Fuoco e larghezza del fumo sono collegati. I nuovi comandi `world auto` cambiano ID e ricreano l'effetto, anche nello stesso punto.

Intervalli conservativi di scala della fiamma: tiny 0,25–0,45; small 0,55–0,75; medium 0,85–1,10; large 1,20–1,50; huge 1,60–1,80. La larghezza del fumo è limitata a 0,55–1,30; salita a 0,90–1,10 e densità a 0,85–1,05 rispetto ai parametri di questo grafo. `size base` imposta i quattro fattori a 1, ma è la nuova base alleggerita, non l'esatta resa della v0.6.

Le dimensioni più estreme della v0.7 non vengono riproposte nel primo collaudo dopo il crash.

## È necessaria una piccola ricompilazione del WASM

Unire i file non basta a ottenere parametri diversi e stabili per ogni generazione. Per questo il kit aggiorna **Module.cpp**, aggiunge **UnifiedParams.h** e include protocol.h. **Non modifica la soluzione, il .vcxproj, il toolset SDK o i post-build già funzionanti.** Non aggiungere un secondo Module.cpp al progetto.

Il wire mantiene 1120 byte, ma usa **versione 2** e aree separate **FireOps.Snapshot.v2 / FireOps.Ack.v2**. I vecchi client non comandano questo modulo. Il nuovo client deve ricevere ACK versione 2.

Formato cella invariato: l'ID uint32 contiene profilo nei bit 31–30, classe nei bit 29–27 e seed nei bit 26–0. HP e quota non vengono usati per nascondere parametri. La correzione EGM96 e il suo codice restano invariati.

Il bridge accetta un solo incendio e soltanto il GUID unificato. `test on`/spawn attached è disabilitato in questa prova. La randomizzazione multiplayer non è ancora integrata; il server dovrà condividere la stessa generazione, non lasciare che ogni client la sorteggi indipendentemente.

Fonti API consultate:
- https://docs.flightsimulator.com/msfs2024/retail/programming-apis/wasm/vfx-api/fsvfxspawninworld/
- https://docs.flightsimulator.com/msfs2024/retail/programming-apis/wasm/vfx-api/vfx-api/
- https://docs.flightsimulator.com/msfs2024/retail/content-configuration/visualeffects/visual-effects-xml-properties/

## Procedura sicura: PRIMA a simulatore chiuso

1. **Chiudi MSFS, tutti i client FireOps e Visual Studio. Non riaprire la libreria v0.7.** L'installer controlla i processi su Windows e rifiuta di procedere se rileva MSFS o Visual Studio aperti.
2. Estrai il kit in una nuova cartella **C:\FireOps\Unico-v08**. La radice deve contenere `INSTALLA-UNICO.cmd`, `install_unified.py` e `FireOps_Unified_v08.xml`.
3. Avvia **INSTALLA-UNICO.cmd**. Percorsi predefiniti:
   - progetto: **C:\FireOps\SimpleFX**;
   - codice bridge: **C:\FireOps\StandaloneModule\Sources\Code**.
4. L'installer crea un backup esterno, archivia i vecchi grafi/sidecar, aggiorna la libreria, installa il singolo XML e i sorgenti del bridge. Non elimina i vecchi backup, i materiali o le cartelle dei client precedenti.
5. Se compare **STOP**, fermati e invia il messaggio. Non copiare a mano tutto payload, tools o tests.

Verifica senza scritture o percorsi personalizzati:

```powershell
py -3 install_unified.py --project "C:\FireOps\SimpleFX" --code "C:\FireOps\StandaloneModule\Sources\Code" --check
```

## Compila il bridge, senza riparare o reinstallare SDK

6. A simulatore ancora chiuso, apri in Visual Studio 2022 la soluzione esistente:

```text
C:\FireOps\StandaloneModule\Sources\Code\StandaloneModule.sln
```

7. Usa la configurazione già funzionante **Debug | MSFS** e **Build → Rebuild Solution**. Lo stesso post-build del progetto deve aggiornare il modulo in PackageSources\modules.
8. Se la compilazione fallisce, invia **il primo errore completo**. Non cambiare versione SDK, toolset o firme API e non procedere alla prova grafica. Il solo header dei parametri è stato compilato localmente in C++, non l'intero modulo con il tuo SDK Windows.

## Poi riapri MSFS: prima Build, NON subito Load In Editor

9. Avvia MSFS. Nel Project Editor apri il progetto standalone **StandaloneModuleProject.xml** già usato in precedenza ed esegui **Build All**, per aggiornare il pacchetto con il WASM appena compilato. Usa il percorso/progetto standalone già funzionante, non quello di SimpleFX per questo passaggio.
10. Nel Project Editor apri **C:\FireOps\SimpleFX\SimpleFX.xml** ed esegui **Build All**. Non serve esportare. **Non cliccare Load In Editor sulla vecchia libreria prima che questa nuova build sia riuscita.**
11. Leggi l'esito senza filtro testuale; Autoset disattivato se nasconde righe. Se ci sono errori pertinenti, inviali prima di continuare. Non dedurre l'esito dai soli contatori generali della sessione.
12. Solo dopo la build riuscita, apri la libreria con **Load In Editor**. Per FireOps deve esserci solo **FireOps_Unified_v08**. EngineSmoke può restare presente come sample. Se vedi ancora decine di FireOps_R07, fermati: non è la libreria ripulita.
13. Ripeti, se necessario, **Load nel Material Inspector** per **FireOps_Flame_v02** e **FireOps_Smoke_Dense_v06**. Non avviare l'effetto dall'editor mentre usi il client.

## Primo collaudo: piccolo, non huge

14. Carica un volo e lascia l'aereo fermo a terra. Avvia solo:

```text
C:\FireOps\Unico-v08\TestLocale\AVVIA.cmd
```

15. **Attendi ACK versione 2.** Se manca, il nuovo bridge non è ancora caricato: non usare il vecchio client Random-v07 e non insistere con gli spawn.
16. Prova:

```text
size tiny
effects both
world auto
```

17. Attendi 30 secondi. Per questa versione **live deve essere 1 anche con both**, perché fiamma e fumo sono emettitori dello stesso effetto. failed atteso 0, heartbeat crescente.
18. Se editor e scena restano stabili, passa a:

```text
size medium
world auto
```

19. Solo dopo il collaudo minimo, per sorteggio libero:

```text
size auto
world auto
```

Ogni ulteriore `world auto` ricrea una combinazione con parametri diversi. Le dimensioni restano bloccate durante la singola generazione. I comandi `effects fire` / `effects smoke` richiedono sempre un successivo `world auto` e disabilitano gli emettitori dell'altro tipo tramite i parametri di emissione.

`size base` sceglie fattori 1 alla prossima generazione. `random on/off` e `variant base` della v0.7 non appartengono a questo client semplificato.

Diagnostica e uscita:

```text
status
clear
quit
```

Invia prima il risultato della compilazione del bridge e del caricamento della libreria, poi lo screenshot della prova tiny. Se l'editor continua a crashare anche con un unico grafo, interrompi le prove e invia il momento preciso ed eventuale modulo segnalato nel crash log/Visualizzatore eventi: non considerare il problema risolto solo perché il file è unico.

## Backup e ripristino

Backup accanto a SimpleFX, **C:\FireOps\FireOps-backup-unico-v08-...**, con copie dei sorgenti rimossi, vecchia libreria e vecchio codice bridge. Il percorso è riportato in `RISULTATO-INSTALLAZIONE.txt`.

**Attenzione: il ripristino completo può riportare i 60 grafi della v0.7 che erano presenti prima del crash. Non usarlo per poi riaprire subito quella libreria.** Serve soprattutto a recuperare il lavoro o a tornare a una revisione stabile con una procedura guidata.

Con MSFS, client e Visual Studio chiusi, il comando tecnico è:

```powershell
py -3 install_unified.py --project "C:\FireOps\SimpleFX" --code "C:\FireOps\StandaloneModule\Sources\Code" --restore "C:\FireOps\FireOps-backup-unico-v08-..."
```

Il ripristino verifica hash e rifiuta modifiche successive, per non sovrascrivere il tuo lavoro. Ripristina sorgenti, non binari già compilati: sarà necessario ricompilare bridge e pacchetti. I backup precedenti v0.2–v0.7 non vengono spostati né cancellati.

## Cosa è stato verificato

Test locali: un solo VisualEffect; quattro emettitori/capacità 256; unicità e collegamenti GUID; parametri; wire versione 2; nuovi ID; confronto dei parametri calcolati in Python e C++ su 2.121 casi; archiviazione dei 60 grafi e dei vecchi grafi separati; conservazione dei materiali; aggiornamento/ripristino protetto di libreria e sorgenti bridge.

**Non è stato compilato l'intero WASM contro l'SDK Windows, né aperto questo grafo in MSFS.** I test non certificano assenza di crash o prestazioni. La distribuzione contiene sorgenti da compilare, non un .wasm già pronto.

`tools/source` e `tests/fixture` contengono input offline dei test, non grafi installati nel progetto. L'installer usa un solo XML VFX: quello nella radice del kit. Il materiale emissivo esistente resta invariato; nessuna luce dinamica su terreno/aereo viene aggiunta in questa revisione.
