from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0



        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """

        relazioni = TourDAO.get_tour_attrazioni() or []  # Recupero tutte le relazioni tour
        # Ciclo su tutte le relazioni
        for relazione in relazioni:
            tour_id = relazione["id_tour"]  # Estraggo gli id di tour e attrazione dalla riga corrente
            attrazione_id = relazione["id_attrazione"]
            tour = self.tour_map[tour_id]  # oggetto Tour# Recupero l'oggetto Tour corrispondente dall'id
            attrazione = self.attrazioni_map[attrazione_id]  # oggetto Attrazione
            tour.attrazioni.add(attrazione)  # Aggiorno il set delle attrazioni del tour
            attrazione.tour.add(tour_id)

    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1


        if max_giorni is not None: #uso il vallore dato dall'utente
            self.max_giorni = max_giorni
        else:
            self.max_giorni = float('inf') #imposto una durata illimitata

        if max_budget is not None:
            self.max_budget = max_budget #uso il vallore dato dall'utente
        else:
            self.max_budget = float('inf') #imposto un budget illimitato

        # Seleziono i tour della regione scelta
        candidati = []
        for tour in self.tour_map.values():
            if tour.id_regione == id_regione:
                candidati.append(tour)

        # Chiamo la ricorsione con valori iniziali
        self._ricorsione(candidati,
                             start_index=0,
                             pacchetto_parziale=[],
                             durata_corrente=0,
                             costo_corrente=0,
                             valore_corrente=0,
                             attrazioni_usate=set())



        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self,candidati, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, attrazioni_usate: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        # Caso terminale: ho considerato tutti i tour disponibili
        if start_index >= len(candidati):
            # confronto il valore corrente con quello ottimale trovato finora
            if valore_corrente > self._valore_ottimo:
                # aggiorno il pacchetto ottimo e le altre informazioni
                self._pacchetto_ottimo = pacchetto_parziale.copy()  # copia della lista corrente
                self._valore_ottimo = valore_corrente # aggiorno valore ottimo
                self._costo = costo_corrente
            return
        # Tour corrente da considerare
        tour = candidati[start_index]
        self._ricorsione(candidati, start_index + 1,  #passo al tour successivo
                         pacchetto_parziale,
                         durata_corrente,
                         costo_corrente,
                         valore_corrente,
                         attrazioni_usate)

        #Controllo dei vincoli prima di includere il tour
        if (durata_corrente + tour.durata_giorni <= self.max_giorni and
                costo_corrente + tour.costo <= self.max_budget and
                tour.attrazioni.isdisjoint(attrazioni_usate)):
            # Aggiorno valori parziali inserendo il tour
            pacchetto_parziale.append(tour)
            nuove_attrazioni = tour.attrazioni - attrazioni_usate # Calcolo le nuove attrazioni aggiunte dal tour
            attrazioni_usate.update(nuove_attrazioni) #vincolo di attrazioni uniche
            valore_aggiunto =sum(a.valore_culturale for a in nuove_attrazioni) # Sommo il valore culturale delle nuove attrazioni

            # Ricorsione con il tour incluso
            self._ricorsione(candidati, start_index + 1,
                             pacchetto_parziale,
                             durata_corrente + tour.durata_giorni,
                             costo_corrente + tour.costo,
                             valore_corrente + valore_aggiunto,
                             attrazioni_usate)

            # Backtracking
            pacchetto_parziale.pop()
            attrazioni_usate.difference_update(nuove_attrazioni)