# FireOps LAN — MSFS 2024
## Prototipo sorgente 0.1 • Guida operativa in italiano

**Leggere prima:** questo archivio contiene un prototipo implementato, NON un addon completo già compilato e certificato in MSFS. Il server e il protocollo hanno test automatici eseguiti; il bridge WASM, SimConnect Windows e i grafi VFX richiedono compilazione e collaudo nel tuo SDK/simulatore. Non sono inclusi SDK Microsoft, DLL Microsoft, `.wasm` precompilati o effetti `.spb` compilati. La parte locale qui non eseguibile è esplicitamente indicata sotto: non basta copiare lo ZIP in Community.

Il tuo primo obiettivo è **vedere un VFX controllato dal bridge**, poi l'incendio statico nel mondo, solo dopo provare gli sganci in due. Non debuggare asset, bridge e rete tutti insieme.

## 1. Cosa è incluso e cosa no

| Funzione | Questa versione |
|---|---|
| Indipendenza dal modello di aereo | Client legge SimVars standard; WASM standalone, nessuna modifica a `panel.cfg` |
| Serbatoio | Virtuale, 2000 L per pilota, sganci di 500 L |
| Incendio | Una cella per missione creata con `here`; il protocollo supporta fino a 32 |
| Dispatcher | Testuale automatico: assegnazione, coordinate, esito sgancio, acqua, completamento e annullamento |
| Multiplayer | Server LAN/VPN autoritativo, snapshot 2 Hz, ingresso a missione iniziata |
| Effetti | Fiamma e fumo locali su ogni PC, istanze create/distrutte dal WASM |
| Diagnostica | Heartbeat, sequenza, numero istanze, fallimenti, eccezioni SimConnect |
| Grafica | Sprite e generatore di grafi VFX base; materiali da creare/compilare nell'editor |
| Rifornimento | Comando a terra, velivolo fermo; non scooping |
| NON incluso | Voce radio, pannello in cockpit, getto d'acqua visivo, fisica balistica, vento/incendio propagante, carriera MSFS, installer, server pubblico, persistenza, riconnessione automatica |

**“Qualsiasi aereo” significa compatibilità architetturale tramite serbatoio virtuale**, non verifica di ogni addon esistente, né collegamento ai serbatoi reali del Canadair o degli addon commerciali. Peso/centraggio non vengono modificati. Gli sganci sono una meccanica semplificata di prossimità, non una simulazione dell'acqua.

Non replichiamo gli aerei: per vedere i velivoli dei tuoi amici usate anche le impostazioni multiplayer native MSFS compatibili tra voi. FireOps replica SOLO la missione, i risultati e gli incendi. Le particelle non saranno identiche fotogramma per fotogramma; posizione, vita della cella e spegnimento vengono dalla stessa autorità.

## 2. Architettura e soluzione al blocco dello spawn

```text
HOST LAN: server.py — missione, serbatoi, dispatcher, validazione sganci
        ↕ TCP 8765, JSON a righe, snapshot completi
OGNI PC: client.py — telemetria SimConnect e comandi da console
        ↕ ClientData FireOps.Snapshot.v1 / FireOps.Ack.v1
OGNI MSFS: FireOps.wasm standalone — VFX API
        → fsVfxSpawnInWorld(GUID, lat/lon/quota)
        → fsVfxDestroyInstance al termine
```

SimConnect non interpreta un GUID VFX come titolo di SimObject. Un eventuale `AICreateSimulatedObject` richiede un SimObject appropriato: non è la chiamata per istanziare direttamente un effetto. Qui **eliminiamo quella dipendenza** e utilizziamo la VFX API dal WASM. L'API richiede effetti già definiti e caricati; non basta inventare un GUID. GUID del materiale, dell'effetto, del modello e object ID SimConnect sono cose diverse. [1](https://docs.flightsimulator.com/msfs2024/retail/programming-apis/wasm/vfx-api/fsvfxspawninworld/)

I fallimenti documentati comprendono GUID non caricato e distanza oltre l'emissione massima. Un ID valido, inoltre, non dimostra che il materiale sia visibile. Il test su aereo serve a separare problemi di asset da quelli di coordinate. [1](https://docs.flightsimulator.com/msfs2024/retail/programming-apis/wasm/vfx-api/fsvfxspawninworld/)

## 3. Preparare Windows

1. Estrai tutto in `C:\FireOps`, evitando di lavorare dentro lo ZIP.
2. Installa Python **3.11 o successivo, 64 bit**. Server/client usano solo libreria standard, niente `pip install SimConnect`.
3. Installa Visual Studio con strumenti C++ e l'integrazione/toolset del tuo **SDK MSFS 2024**. Usa una versione Visual Studio supportata dall'installer del tuo SDK.
4. In MSFS abilita Developer Mode. Annota versione simulatore e SDK, e se sei su retail o beta: devono essere coerenti.
5. Da PowerShell:

```powershell
cd C:\FireOps
py -3 --version
py -3 -c "import struct; print(struct.calcsize('P')*8)"
py -3 tools\configure_sdk.py "C:\MSFS 2024 SDK"
py -3 -m unittest discover -s tests -v
```

Il secondo comando deve stampare `64`. Sostituisci il percorso SDK con quello reale. `configure_sdk.py` genera `wasm\VfxSdk.h` usando l'header effettivamente installato e mostra le DLL trovate. È preferibile a supporre che il nome dell'header sia uguale in tutte le revisioni SDK.

Per un elenco dei sample puoi anche usare:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_sdk.ps1 -Sdk "C:\MSFS 2024 SDK"
```

`Bypass` qui si applica al processo del comando, non chiede di disabilitare permanentemente la policy. Lo script elenca file locali, non scarica né esegue codice da Internet.

## 4. Primo cancello: un effetto SDK visibile

Prima di compilare FireOps:

1. Cerca nel tuo SDK il sample **SimpleFX**, copialo in una cartella di lavoro. Non modificare l'originale dentro SDK.
2. Nel menu Developer Mode → File → Open Project, apri `SimpleFX.xml`.
3. Nel Project Editor usa **Build All In Project**. Verifica che non ci siano errori.
4. Seleziona l'asset group `VisualEffectsLib` → **Load In Editor**.
5. Apri `EngineSmoke.xml` nel VFX Editor.
6. Nel debugger/spawner seleziona un contact point dell'aereo e premi Spawn.
7. Usa camera esterna, velivolo fermo, scena completamente caricata. Devi vedere il fumo.

Questa è la procedura del sample ufficiale; il progetto comprende anche la libreria materiali. [2](https://docs.flightsimulator.com/msfs2024/html/7_Samples_Tutorials/Samples/Misc/SimpleFX.htm)

**Se il sample non appare, fermati qui:** il problema non è il server FireOps. Controlla console build, materiale, caricamento del package e distanza della camera.

Per il primo test FireOps puoi usare il GUID di `EngineSmoke`: copialo dal blocco `VisualEffect.VisualEffect` (`InstanceId`) o dal debugger Asset Packages. Mettilo temporaneamente in `flame_guid`; `smoke_guid` resta vuoto. Vedrai fumo, non una fiamma: è deliberatamente un test di collegamento con un asset già funzionante.

Non copiare un GUID di esempio dalla documentazione aspettandoti che l'effetto sia installato. Per testare dopo un riavvio copia in Community **entrambi i pacchetti compilati del sample**, effetto e MaterialLib, dalla cartella `Packages`. Evita due copie dello stesso package contemporaneamente montate, una da DevMode e una da Community.

## 5. Compilare il bridge WASM

Il template ufficiale da usare è **MSFS 2024 WASM Standalone Module**, non gauge, non sistema installato su un singolo velivolo e non template 2020. [3](https://docs.flightsimulator.com/msfs2024/retail/programming-apis/wasm/creating-a-wasm-project/)

1. Apri Visual Studio → Create a New Project → cerca `MSFS`.
2. Seleziona **MSFS 2024 WASM Standalone Module**, nome `FireOpsBridge`.
3. Rimuovi dalla compilazione il `.cpp` generato che contiene `module_init`/`module_deinit`, per evitare simboli duplicati.
4. Aggiungi al progetto come file esistenti:
   - `C:\FireOps\wasm\FireOps.cpp`
   - `C:\FireOps\wasm\protocol.h`
   - `C:\FireOps\wasm\VfxSdk.h`
5. Conserva le impostazioni del template SDK per include, linker, esportazioni e piattaforma WASM/MSFS. Abilita C++17 se non già attivo. **Non compilare questo progetto come eseguibile Windows x64.**
6. Se `SimConnect.h` non è trovato, aggiungi agli include la directory del SimConnect SDK installato che lo contiene. Se il linker non risolve SimConnect, confronta le impostazioni con il sample SDK `StandaloneModule`: per il WASM usa l'integrazione/import del toolset, non la DLL nativa Windows.
7. Build in configurazione Release. Annota il percorso esatto del `.wasm` generato.
8. Crea il package con il modulo compilato:

```powershell
cd C:\FireOps
py -3 tools\package_wasm.py "C:\percorso\reale\FireOpsBridge.wasm"
```

9. Copia la cartella `C:\FireOps\packages\fireops-bridge` nella **Community effettiva della tua installazione 2024**. Individua il percorso dal sistema di gestione pacchetti/Virtual File System di DevMode; non supporre un percorso Steam o Store universale.
10. Struttura finale, senza un livello di cartella in più:

```text
Community/
  fireops-bridge/
    manifest.json
    layout.json
    modules/
      FireOps.wasm
```

11. Riavvia MSFS, carica un volo libero e attendi la compilazione/caricamento WASM. Nel debug WASM/console cerca:

```text
[FireOps] bridge initialized protocol=1 packet=1120
```

La riga indica che l'inizializzazione è arrivata in fondo; controlla anche eventuali HRESULT/eccezioni precedenti. Se il package minimal non viene caricato nella tua build, usa l'involucro del sample **StandaloneModule** del tuo SDK per distribuire lo stesso `.wasm` e ricostruisci dal Project Editor. Il package generato qui non è stato verificato nel simulatore.

Non usare hot reload come prima prova: il bridge crea le aree ClientData all'avvio e una ricarica parziale può lasciare stato precedente. Chiudi il client e riavvia MSFS dopo modifiche al modulo.

## 6. Avviare server e primo client sullo stesso PC

PowerShell A:

```powershell
cd C:\FireOps
py -3 app\server.py --token "CAMBIA-CHIAVE-GRUPPO-2024" --admin "CAMBIA-CHIAVE-HOST-2024"
```

Per l'uso effettivo scegli **due chiavi differenti**, almeno 12 caratteri, e modifica anche i file client. La chiave host non va distribuita agli altri piloti.

PowerShell B:

```powershell
cd C:\FireOps
Copy-Item client.example.json client.json
notepad client.json
```

Configura:

- `host`: `127.0.0.1` solo sul PC che esegue anche server.
- `simconnect_dll`: percorso della DLL **nativa x64** del SDK; NON `Microsoft.FlightSimulator.SimConnect.dll` managed. Usa gli slash `/` in JSON o raddoppia `\\`.
- `flame_guid`: GUID reale del fumo del sample per questo primo test.
- `smoke_guid`: stringa vuota.
- `token`, `admin`: uguali a quelli del server.

Poi, con MSFS già in volo:

```powershell
py -3 app\client.py --config client.json
```

Attendi telemetria e heartbeat. Il client non deve stampare continuamente `BRIDGE NON PRONTO`.

Scrivi `status`, Invio. I valori ACK sono:

```text
version / seq / heartbeat / live / failed / exception
```

- `heartbeat` aumenta ogni secondo: WASM vivo e canale ACK funzionante.
- `seq` deve avanzare quando il client invia: anche il canale snapshot funziona.
- `live`: istanze VFX che il bridge considera valide.
- `failed`: tentativi falliti nell'ultimo tick, non un totale storico.
- `exception`: ultimo codice eccezione SimConnect, 0 se nessuna ricevuta.

Se avvii il client prima del bridge, la sottoscrizione ACK può fallire: avvia correttamente il WASM e **riavvia il client**.

## 7. Secondo cancello: spawn via WASM

Nel client:

```text
test on
```

Questo usa `fsVfxSpawnOnSimObject` sullo user aircraft, senza modificarlo. Guarda da fuori e attendi qualche secondo per texture/caricamento. Il VFX è attaccato alla radice con offset di test: la posizione esatta rispetto alla fusoliera varia col modello. Se è nascosto usa un aereo piccolo per la diagnostica.

Devi avere `live >= 1` e vedere il sample. Poi:

```text
test off
```

L'effetto deve scomparire. **Questo passaggio dimostra asset + bridge + comando**, ma non ancora la quota nel mondo.

## 8. Terzo cancello: incendio statico nel mondo

1. Metti l'aereo a terra e fermo in un punto pianeggiante facile da ritrovare. Per la prima prova va bene un'area libera dell'aeroporto; non cominciare da montagne o incendi a 100 km.
2. Aspetta almeno 2 secondi per la telemetria.
3. Nel client host:

```text
here
```

4. Il dispatcher pubblica coordinate e nuova missione.
5. Il server usa **latitudine/longitudine correnti e GROUND ALTITUDE locale + 1 m**, non quota dell'aereo in piedi, né quota zero globale.
6. Allontanati lentamente o usa camera drone: l'effetto deve restare fermo sul terreno mentre l'aereo si sposta.
7. `cancel` annulla la missione e rimuove l'effetto su tutti i client.

Il comando crea la cella **sotto la posizione attuale**, non un punto lontano: così evitiamo di fingere che la quota del terreno sotto l'aereo valga anche altrove. Per scenari remoti serve un rilevamento terreno dedicato, non incluso in 0.1.

### Se l'effetto è sotto terra o sospeso

Esiste una segnalazione di offset altimetrico dipendente dalla posizione per `fsVfxSpawnInWorld` nella versione 1.7.16; non equivale a una conferma che la tua versione sia affetta o che il problema sia ancora presente. [4](https://devsupport.flightsimulator.com/t/vfx-api-fsvfxspawninworld-altitude-offset/17709)

- Controlla prima GUID, distanza, materiale e unità: nel progetto le quote sono in **metri**.
- `altitude_bias_m` nel client consente una correzione **solo diagnostica locale** (es. +10, +30, poi -10); riavvia il client per applicarla.
- Non usare una correzione trovata a Bari come soluzione globale: geoid/ellipsoid/referential richiedono verifica sulla specifica API SDK.
- In SDK beta possono cambiare firma e opzioni della funzione. Questo sorgente usa la firma retail documentata a sei argomenti. Se il tuo header richiede parametri diversi, adegua la singola chiamata dopo aver letto l'header, senza mescolare DLL/header/toolset di revisioni diverse.

## 9. Creare fiamma e fumo propri

**È un passaggio di authoring necessario**, non già compilato in questo archivio. Hai sprite e un generatore XML per ridurre il lavoro. Non sostituisce la validazione dell'editor.

1. Da una copia funzionante di SimpleFX crea/duplica nel Material Editor due materiali VFX con GUID nuovi: `FireOps_FlameMat` e `FireOps_SmokeMat`.
2. Usa `assets\flame.png` e `assets\smoke.png` come texture dei due materiali. Conserva uno shader/blending adatto alle particelle prendendo il materiale del sample come riferimento.
3. Fiamma: trasparenza e componente emissiva; fumo: trasparenza senza emissione. Non usare materiali opachi.
4. Salva e compila la MaterialLib. Copia i GUID reali dei due materiali dal Material Editor.
5. Genera i grafi (sostituisci le due stringhe, non sono valori da copiare letteralmente):

```powershell
py -3 tools\make_vfx.py --flame-material "GUID-REALE-MATERIALE-FIAMMA" --smoke-material "GUID-REALE-MATERIALE-FUMO"
```

6. Il comando crea `vfx-source\FireOps_Flame.xml`, `FireOps_Smoke.xml`, `FireOps.vfxlib` e `guids.json`.
7. Copia i tre file XML/VFXLIB nella cartella sorgente di un asset group **VisualEffectsLib** del tuo progetto SDK, ad esempio `PackageSources\VisualEffectLibs\FireOps\`. Il JSON è solo una nota di configurazione, non un asset VFX.
8. Se hai duplicato l'asset group del sample, aggiorna `AssetDir` a questa directory e verifica `OutputDir` coerente con la struttura VisualEffectLibs del sample. Mantieni anche la MaterialLib del punto 4 tra i pacchetti da costruire/distribuire.
9. **Load In Editor**: apri entrambi i grafi, controlla collegamento Material nell'Output, emissione continua e preview. Il generatore usa emitter a tempo, non a distanza, altrimenti un incendio fermo potrebbe non emettere particelle.
10. Build All. Nessun errore di parsing, riferimenti materiali o asset mancanti deve essere ignorato. Gli XML vengono compilati in SPB: copiare soltanto gli XML sorgenti in Community non sostituisce questo passaggio. [5](https://docs.flightsimulator.com/msfs2024/retail/content-configuration/visualeffects/visual-effects/)
11. Copia i pacchetti costruiti di effetti **e materiali** in Community, evita duplicati, riavvia il simulatore.
12. Copia da `guids.json` i due GUID **degli effetti**, non quelli dei materiali, in `client.json`. Riavvia il client e ripeti `test on`/`test off`/`here`.

I grafi hanno una resa dimostrativa: particelle semplici, nessuna animazione flipbook, fade o turbolenza complessa. Puoi migliorarli nel VFX Editor dopo il collaudo. Se il generatore non è accettato dal tuo SDK, usa il grafo del sample già validato e applica i parametri da editor: non è un motivo per tornare a tentare spawn SimObject casuali.

## 10. Multiplayer LAN/VPN, due PC

Sul PC host il server resta aperto. Trova l'IPv4 della scheda LAN con `ipconfig`, per esempio `192.168.1.50`.

Sul secondo PC installa:

- Python x64;
- gli stessi pacchetti compilati bridge/VFX/MaterialLib in Community;
- cartella `app` e configurazione;
- DLL SimConnect nativa appropriata, ottenuta dall'SDK/redistribuzione consentita, non da siti casuali.

Nel suo `client.json`:

```json
{
  "name": "Pilota-2",
  "host": "192.168.1.50",
  "port": 8765,
  "token": "CAMBIA-CHIAVE-GRUPPO-2024",
  "admin": "",
  "simconnect_dll": "C:/percorso/reale/SimConnect.dll",
  "flame_guid": "COPIA-IL-GUID-REALE-DELL-EFFETTO",
  "smoke_guid": "COPIA-IL-GUID-REALE-DELL-EFFETTO",
  "altitude_bias_m": 0
}
```

I segnaposto GUID vanno sostituiti. Ogni client parla con **il proprio** MSFS locale: non configurare SimConnect remoto tra i due simulatori.

Se il firewall blocca la connessione, sul solo host aggiungi una regola limitata a rete privata e subnet locale (PowerShell amministratore):

```powershell
New-NetFirewallRule -DisplayName "FireOps LAN TCP 8765" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow -Profile Private -RemoteAddress LocalSubnet
```

Con VPN limita esplicitamente la regola alla subnet VPN effettiva, non a tutto Internet. Dal secondo PC prova:

```powershell
Test-NetConnection 192.168.1.50 -Port 8765
```

Poi avvia MSFS e il client su entrambi. Usa lo stesso scenario e un punto vicino all'incendio; gli effetti lontani possono fallire il primo spawn e saranno ritentati ogni secondo quando ti avvicini.

**Non aprire la porta sul router.** Il protocollo ha chiavi condivise ma non TLS, non anticheat e non autenticazione individuale; va usato solo su LAN fidata o VPN. Il server valida limiti e freschezza ma deve fidarsi della telemetria inviata dai client.

## 11. Eseguire una missione insieme

1. Host fermo a terra nel punto incendio: `here`.
2. Entrambi ricevono la stessa missione. Verifica `status`: medesimo ID, coordinate, HP.
3. Decollate. Sorvolate il punto a **5–100 m AGL**, velocità al suolo **≤100 m/s**.
4. In prossimità del centro, entro **80 metri orizzontali**, digita `drop`, Invio.
5. Uno sgancio consuma 500 L anche se manca il bersaglio. Un centro toglie 25 HP; quattro centri complessivi estinguono la cella.
6. Attendi almeno 2 secondi fra sganci dello stesso pilota. Più piloti possono contribuire allo stesso incendio.
7. A zero HP entrambi vedono sparire fiamma e fumo e ricevono il completamento dal dispatcher.
8. `refill` ricarica 2000 L solo a terra e sotto 2 m/s. Per il prototipo è consentito ovunque a terra.
9. Un nuovo `here` host crea un'altra missione; `cancel` annulla quella corrente. Non c'è ancora un catalogo o scheduler di scenari.

Per la prima prova usa un velivolo semplice; dopo ripeti cambiando aereo senza toccare i suoi file. Non scrivere comandi mentre hai bisogno di pilotare manualmente a bassa quota: usa un secondo operatore o una fase di volo stabilizzata per il collaudo nel simulatore.

## 12. Diagnostica rapida

| Sintomo | Controllo successivo |
|---|---|
| Nessuna connessione SimConnect | Volo libero caricato, DLL nativa corretta, Python x64; elimina solo eventuali configurazioni remote errate dopo averne fatto backup |
| DLL non caricabile / WinError 193 | Probabile DLL managed o bitness sbagliata |
| `BRIDGE NON PRONTO` | Modulo standalone montato? Log `bridge initialized`? Errori WASM? Client avviato dopo bridge? |
| Heartbeat sì, seq fermo | ClientData snapshot non ricevuta; ABI/nomi/versioni uguali, nessuna seconda istanza client |
| `failed > 0` | Effetto GUID inesistente/non montato oppure troppo lontano; prova sample a 20 m |
| `live > 0`, invisibile | MaterialLib mancante, alpha/blending, geometria coperta, quota, culling; non solo problema di rete |
| Test aereo OK, mondo KO | Metri contro piedi, quota/referential e coordinate; prova terreno piano e bias diagnostico |
| VFX segue l'aereo | Hai ancora `test on`; spegnilo. La missione usa world spawn |
| Il fuoco compare solo su un PC | Pacchetti/GUID differenti, client non connesso, effetto fuori range o WASM non caricato sull'altro |
| Sgancio rifiutato | Leggi messaggio: AGL, on_ground, velocità, serbatoio, cooldown o telemetria vecchia |
| Dopo chiusura server restano effetti | Client dovrebbe inviare clear; in crash il WASM li elimina dopo circa 6 tick senza snapshot, se il timer sim continua |
| Eccezione SimConnect | Conserva numero, sendID e index dal log; non basta il solo HRESULT della chiamata |

Una sola istanza di `client.py` per simulatore: i nomi ClientData sono condivisi localmente. Dopo perdita rete/server riavvia il client; riceve uno snapshot completo. Il pilota riconnesso è nuovo e il serbatoio si resetta: comportamento da prototipo, non anticheat.

## 13. Test di accettazione da registrare

- [ ] SimpleFX visibile dall'editor.
- [ ] Build WASM con il tuo SDK senza errori.
- [ ] Package bridge caricato dopo riavvio e heartbeat crescente.
- [ ] `test on` crea il sample, `test off` lo distrugge.
- [ ] `here` crea un effetto fermo nel mondo con quota corretta.
- [ ] Fiamma/fumo propri montati insieme alla MaterialLib.
- [ ] Due PC mostrano stesso ID missione e HP.
- [ ] Un pilota entra a missione iniziata e riceve lo stato corrente.
- [ ] Sganci dei due piloti aggiornano una sola missione e consumano i rispettivi serbatoi.
- [ ] Completamento e `cancel` rimuovono gli effetti su entrambi.
- [ ] Cambio di velivolo e ripetizione della prova.
- [ ] Perdita collegamento ripulisce gli effetti, riavvio client risincronizza.

## 14. Test realmente eseguiti qui

`TEST_RESULTS.txt`: **11 test Python superati**, inclusa connessione TCP di due client simulati, ingresso tardivo e rifiuto dei comandi host da parte del pilota. Testano server/logica/protocollo, NON due istanze MSFS.

Verificato inoltre layout C++ con compilazione `protocol.h` su Linux (1120 byte snapshot / 24 byte ACK), sintassi Python e correttezza XML formale del generatore. **Non verificati:** compilazione con SDK Microsoft, firma/header nella tua revisione, carregamento package MSFS, spawn/rendering VFX, ctypes contro SimConnect.dll e multiplayer tra simulatori reali. Il check XML non è una compilazione SPB.

Il progetto è quindi una base concreta da collaudare, non una promessa di funzionamento al primo avvio. Per diagnosticare il primo blocco raccogli: versione MSFS/SDK, output di `configure_sdk.py`, primo errore build completo, log `[FireOps]`, output `status` e risultato del sample SimpleFX.
