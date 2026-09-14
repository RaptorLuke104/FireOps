# FireOps — Base classica con bridge v2

## Decisione concordata

**Vecchia grafica (fiamma v0.4 + fumo denso v0.6), un solo XML, bridge v2 e randomizzazione attuale del v2.** Non è un ripristino integrale della v0.7: non tornano le 30 coppie/60 grafi, il client v1 o il vecchio protocollo.

Il file installato resta **FireOps_Unified_v08.xml**, con GUID **C0F18F57-0F39-4EC1-8DED-E00C0597A908**. Nell'editor il nome diventa **FireOps_Unified_Classico_v2**. Un solo effetto, quattro emettitori, sei GraphParameter già supportati dal bridge attuale.

## Grafica recuperata

Sono riprese le proprietà dei sorgenti approvati:
- fiamma v0.4: tre emettitori, raggi nominali 3,2 / 2,3 / 3,8 m, emissione 12/10/10 particelle/s, vite e salita originali;
- fumo v0.6: emissione 20/s, vita 18–28 s, salita 6–8 m/s prima del parametro casuale, raggio finale 32 m prima del parametro di larghezza, curve di densità originali;
- materiali originali **FireOps_Flame_v02** e **FireOps_Smoke_Dense_v06**;
- nessun atlas animato e nessuna deformazione delle punte v0.9;
- nessuna delle modifiche successive per ancorare le particelle della fiamma. Torna anche il movimento verso l'alto della vecchia fiamma: è il comportamento di quella base, non la fiamma continua modificata.

I parametri del bridge restano FireScale, SmokeWidth, SmokeRise, SmokeDensity, FireOn e SmokeOn. Con `size base` i fattori sono 1. Con `size auto` la combinazione viene sorteggiata a ogni `world auto` e resta stabile durante la generazione. Sono le variazioni e i limiti del bridge v2, non il catalogo v0.7.

## Carico grafico: importante

La vecchia densità richiede più particelle della v0.8 alleggerita: **64 + 64 + 64 + 640 = 832 di capacità totale**, non 256. Capacità non significa che siano tutte vive continuamente. L'installer aggiorna, se riconosce la vecchia frase, soltanto l'etichetta del client che dichiarava 256; non ne modifica il comportamento o il protocollo.

Il bridge v2 mantiene il limite di **un incendio alla volta**. Un solo XML elimina il catalogo da 60 grafi che era presente durante il crash dell'editor, ma non garantisce assenza di crash né prestazioni equivalenti alla versione alleggerita. Anche dimensione e sovrapposizione dei quad del fumo aumentano il costo GPU.

Prima prova `size base`; non cominciare da huge. Questa combinazione con il bridge v2 non è ancora collaudata nel simulatore.

## Installazione, senza vecchi comandi di ripristino

Funziona sopra la base unificata v0.8 oppure sopra Punte-v0.9, purché i materiali base siano ancora presenti. Non serve forzare i vecchi ripristini che si fermavano per XML modificato: viene salvata una nuova copia dello stato attuale prima di sostituire il grafo.

1. Nel client: `clear`, poi `quit`.
2. **Chiudi MSFS.** Non occorre modificare o ricompilare Visual Studio.
3. Estrai lo ZIP in **C:\FireOps\BaseClassica-v2**.
4. Esegui **INSTALLA-BASE.cmd**. Progetto predefinito: **C:\FireOps\SimpleFX**. Se compare STOP, invia il messaggio prima di proseguire.
5. Riapri MSFS, apri **SimpleFX.xml** nel Project Editor ed esegui **Build All solo su SimpleFX**.
6. Se la build riesce, riapri la libreria con **Load In Editor**. Deve esserci **FireOps_Unified_Classico_v2**, non 60 varianti.
7. Se necessario, esegui **Load nel Material Inspector** di **FireOps_Flame_v02** e **FireOps_Smoke_Dense_v06**, non del materiale Tips_v09.

**Non eseguire INSTALLA-UNICO o INSTALLA-RANDOM. Non usare il client Random-v07. Non ricompilare il WASM.** I vecchi asset del materiale Tips_v09 possono restare sul disco, ma non sono referenziati da questo grafo e non vengono cancellati.

## Prova e passaggio alle missioni

Usa sempre:

```text
C:\FireOps\Unico-v08\TestLocale\AVVIA.cmd
```

Con aereo fermo a terra, attendi ACK v2, poi:

```text
effects both
size base
world auto
```

Attendi 30–40 secondi. Il risultato atteso del bridge resta **live 1, failed 0**, perché fuoco e fumo fanno parte della stessa istanza. Se al riavvio manca ACK v2, verifica il caricamento del pacchetto standalone già compilato come nel precedente collaudo; non tornare ai client v1.

Una volta confermata la base e la fluidità, per il sorteggio:

```text
size auto
world auto
```

Non cambia il limite di un incendio: un nuovo world auto sostituisce quello precedente. I comandi `effects fire` e `effects smoke` restano disponibili. L'aspetto e l'altezza possono variare rispetto a una singola schermata precedente per fase delle particelle, camera e parametri casuali: non è una riproduzione pixel per pixel di uno screenshot.

Dopo il controllo minimo, questa base viene congelata e il lavoro può proseguire su dispatcher e missioni. Il vecchio client LAN/protocollo v1 non è ancora integrato con questo bridge v2.

## Backup

Il backup nuovo si trova accanto a SimpleFX: **C:\FireOps\FireOps-backup-baseclassica-v2-...**. Il percorso preciso è scritto in `RISULTATO-INSTALLAZIONE.txt`. Vengono conservati l'XML attuale e, se aggiornata, la sola copia del file client con la precedente etichetta. Materiali, texture, libreria, protocollo e sorgenti WASM non vengono modificati.

Verifica senza scritture:

```powershell
py -3 install_base.py --project "C:\FireOps\SimpleFX" --client "C:\FireOps\Unico-v08\TestLocale" --check
```

Per annullare questa applicazione, a MSFS e client chiusi, usando il percorso completo del backup:

```powershell
py -3 install_base.py --project "C:\FireOps\SimpleFX" --client "C:\FireOps\Unico-v08\TestLocale" --restore "C:\FireOps\FireOps-backup-baseclassica-v2-..."
```

Il ripristino protegge da modifiche successive: non forza la sovrascrittura di file modificati. Dopo serve Build All su SimpleFX. Conserva tutti i backup precedenti.

## Verifiche locali

Sei test: effetto unico, quattro emettitori/capacità 832, rate/curve/vite originali, GUID e parametri v2, riferimenti validi, xVariant scalari (correzione dell'errore SDK già risolto), assenza atlas, installazione limitata a XML ed eventuale etichetta client, ripristino protetto.

`TEST_RESULTS.txt` contiene l'esito. Non è stata eseguita una compilazione SDK/Windows né una prova di rendering o prestazioni. Gli input originali e il generatore sono in tools; tests/fixture non va installata né aperta nel simulatore.
