import pygame
import random
import sys
import time
import math
import numpy as np

pygame.init()



# WEKTOR MIĘDZY ŚRODKAMI
def middle(atom_1, atom_2):
    ws = pygame.math.Vector2()
    ws.x = atom_1.position.x - atom_2.position.x
    ws.y = atom_1.position.y - atom_2.position.y
    return ws


# ZAMIANA SKŁADOWYCH PRZY ZDERZENIU
def exchange(atom1, atom2):
    odleglosc = math.sqrt(
        (atom2.position.x - atom1.position.x) ** 2 + (atom2.position.y - atom1.position.y) ** 2)
    sin = (atom1.position.y - atom2.position.y) / odleglosc
    cos = (atom1.position.x - atom2.position.x) / odleglosc

    matrix = np.array([[sin, -cos], [cos, sin]])
    m_1 = np.array([[atom1.velocity.x], [atom1.velocity.y]])
    m_2 = np.array([[atom2.velocity.x], [atom2.velocity.y]])

    a_1 = np.matmul(matrix, m_1)
    a_2 = np.matmul(matrix, m_2)

    # print(a_1)
    # print(a_2)

    v_1_pionowa = a_1[0][0]
    v_1_pozioma = a_2[1][0]
    v_2_pionowa = a_2[0][0]
    v_2_pozioma = a_1[1][0]

    mat_1 = np.array([[v_1_pozioma], [v_1_pionowa]])
    mat_2 = np.array([[v_2_pozioma], [v_2_pionowa]])

    vk_1 = np.matmul(matrix, mat_1)
    vk_2 = np.matmul(matrix, mat_2)

    # print(vk_1)
    # print(vk_2)
    atom1.velocity.y = vk_1[0][0]
    atom1.velocity.x = vk_1[1][0]
    atom2.velocity.y = vk_2[0][0]
    atom2.velocity.x = vk_2[1][0]

    return



class Pomiary:

    # KONFIGURACJA
    def __init__(self, sym):

        self.powierzchnia = sym.screen                          # powierzchnia do rysowania
        self.N = 0                                              # ilość zderzeń
        self.droga = 0                                          # łączna droga
        self.droga_sr = 0                                       # średnia droga
        self.points = []                                        # współrzędne zderzeń (do rysowania ścieżki)
        self.points.append(pygame.Vector2())                    # punkt początkowy
        self.points[0].x, self.points[0].y = 0 + sym.R, sym.a - sym.R
        self.points.append(pygame.Vector2())
        self.points[1].x, self.points[1].y = 0, 0

        return

    # RYSOWANIE ŚCIEŻKI
    def sciezka(self):
        pygame.draw.lines(self.powierzchnia, (250, 250, 250), False, self.points)
        return


class Symulacja:

    # KONFIGURACJA
    def __init__(self, pro, nl, ran, licz, timer):

        self.R = pro                            # promień atomu
        print("\nDlugosc promienia:\t", self.R)
        self.d = self.R/10                      # dopuszczalny błąd
        print("Dopuszczalny blad:\t", self.d)
        self.nH = nl                            # nH = nL
        self.a = self.nH * self.R
        self.K = 20                             # k >= min(nH)
        # print("K:\t", self.K)
        self.v_range = ran                      # zakres prędkości
        print('Zakres predkosci:\t', self.v_range)

        self.qt = 1/(self.K * self.v_range)     # delta t wg instrukcji
        # print("Delta_t:\t", self.qt)
        self.wym = (self.a, self.a)             # wymiary ekranu wg instrukcji a = nH * R
        print("Wymiary ekranu:\t\t", self.wym)
        self.fps = 50                           # frames per second
        # print("FPS:\t", self.fps)
        self.tps = 1.0 / self.fps               # ticks per second
        # print("TPS:\t", self.tps)

        self.screen = pygame.display.set_mode(self.wym)     # powierzchnia wyświetlania
        self.clock = pygame.time.Clock()        # pomiary czasu dla wyświetlania FPS
        self.delta = 0

        self.M = 1                              # masa atomów
        self.ilosc = licz                       # ilość atomów
        print("Liczba atomów:\t\t", self.ilosc)

        '''stosunek czasu do maksymalnej prędkości dobrany tak, 
        żeby podczas jednego cyklu wyświetlania
        atomy nie przesuwały się dalej niż o R'''
        # self.T = math.floor(math.pow(2 * self.a * self.a, 0.5) / self.R)

        self.T = 100
        # print("T:\t\t", self.T)               # czas, w którym ma przelecieć przez przekątną ekranu
        self.atoms = []                         # tablica atomów
        self.check = []                         # tablica sprawdzania zderzeń
        for i in range(0, self.ilosc):
            self.check.append(0)
        # print("Check:\t", self.check)

        self.czas = timer                       # czas trwania symulacji w sekundach
        print("Czas symulacji:\t\t", self.czas)
        self.timer = self.czas                  # czas pomiarowy
        self.pomiary = Pomiary(self)            # obiekt z danymi do drogi

        return

    # INICJALIZACJA
    def inicjalizuj(self):
        self.delta = 0

        # generacja atomu testowego na pierwszym miejscu, aby nic nie pojawilo sie na nim
        atom = Atom(self)
        atom.position.x = 0 + self.R
        atom.position.y = self.a - self.R
        atom.velocity.x = random.randint(1, self.v_range)
        atom.velocity.y = -atom.velocity.x
        print('\nV_test:\t', atom.velocity)
        atom.color = pygame.Color('red')
        self.atoms.append(atom)

        # generacja pozostalych atomow
        for i in range(self.ilosc - 1):
            atom = Atom(self)
            self.atoms.append(atom)

        # zamiana pierwszego z ostatnim, aby testowy byl na koncu listy
        bufor = self.atoms[0]
        self.atoms[0] = self.atoms[-1]
        self.atoms[-1] = bufor

        # przypisanie drugiego punktu sciezki, ktory bedzie modyfikowany
        self.pomiary.points[1].x, self.pomiary.points[1].y = self.atoms[-1].position.x, self.atoms[-1].position.y

        self.delta += self.clock.tick() / 1000
        # print('\nCzas inicjalizacji:\t', self.delta)

        return

    # SYMULACJA
    def run_sym(self):

        trwanie = pygame.time.Clock()
        czas = 0

        while czas <= self.czas:

            self.delta += self.clock.tick() / 1000
            czas += trwanie.tick() / 1000
            for event in pygame.event.get():                    # dla każdego zdarzenia
                if event.type == pygame.QUIT:                   # zamykanie okna bez wysypywania systemu
                    sys.exit(0)

            if self.delta > self.tps:                           # wyświetlanie atomów

                self.delta -= self.tps
                self.screen.fill((0, 0, 0))                     # czyszczenie ekranu

                self.pomiary.sciezka()                          # rysowanie ścieżki

                for i in range(self.ilosc):                     # każdy atom
                    atom = self.atoms[i]
                    atom.move(self)                             # wykonaj ruch
                    self.bandy(i)                               # zderzenia ze ściankami
                    atom.draw(self.screen)                      # narysuj atom

                self.zderzenia()                                # zderzenia z sobą nawzajem

                pos = pygame.Vector2()                          # modyfikacja wyświetlania ścieżki
                pos.x, pos.y = self.atoms[-1].position.x, self.atoms[-1].position.y
                self.pomiary.points[-1] = pos

                pygame.display.flip()                           # odświeżenie ekranu

                for i in range(self.ilosc):                     # odświeżanie sprawdzania zderzeń
                    if self.check[i] > 0:
                        self.check[i] -= 1
                # print("Czas:\t", czas)

        return

    # ZDERZENIA MIĘDZY ATOMAMI
    def zderzenia(self):

        hits = []                                               # lista indeksów zderzających się atomów (jako tuple)
        for i in range(self.ilosc):                             # porównuje każdy z każdym
            atom1 = self.atoms[i]
            for j in range(i + 1, self.ilosc):
                atom2 = self.atoms[j]
                if atom1.position.distance_to(atom2.position) <= 2 * self.R + self.d:
                    akt = (i, j)                                # obecny tuple
                    if (self.check[i] == 0 and self.check[j] == 0) or (self.check[i] != self.check[j]):
                        hits.append(akt)
                        self.check[i] = 10
                        self.check[j] = 10
                        if i == self.ilosc - 1 or j == self.ilosc - 1:
                            self.pomiary.N += 1
                            pos = pygame.Vector2()
                            pos.x, pos.y = self.atoms[-1].position.x, self.atoms[-1].position.y
                            self.pomiary.points.append(pos)

        for t in hits:                                          # dla każdego zderzenia

            atom1 = self.atoms[t[0]]
            atom2 = self.atoms[t[1]]

            exchange(atom1, atom2)

            atom1.banda_poz, atom1.banda_pion = 0, 0
            atom2.banda_poz, atom2.banda_pion = 0, 0

            # odznaczenie w check
            self.check[t[0]] -= 1
            self.check[t[1]] -= 1

        return

    # ZDERZENIA ZE ŚCIANKAMI NACZYNIA
    def bandy(self, i):

        zderzenie = False
        atom = self.atoms[i]

        # zderzenie ze scianka pionowa
        if not 0 + self.R <= atom.position.x <= self.a - self.R and atom.banda_pion == 0:
            atom.velocity.x = -atom.velocity.x
            atom.banda_pion = 10
            atom.banda_poz = 0
            zderzenie = True

        # zderzenie ze scianka pozioma
        if not 0 + self.R <= atom.position.y <= self.a - self.R and atom.banda_poz == 0:
            atom.velocity.y = -atom.velocity.y
            atom.banda_poz = 10
            atom.banda_pion = 0
            zderzenie = True

        if zderzenie and i == self.ilosc-1:     # w przypadku testowego
            pos = pygame.Vector2()
            pos.x, pos.y = atom.position.x, atom.position.y
            self.pomiary.points.append(pos)

        # zmiejszenie licznikow
        if atom.banda_pion > 0:
            atom.banda_pion -= 1
        if atom.banda_poz > 0:
            atom.banda_poz -= 1

        return

    # PODSUMOWANIE
    def podsumowanie(self):

        print('\n--------------------------------\n')
        print('\t P O D S U M O W A N I E \n')
        print('Czas symulacji:\t\t', self.czas)
        print('Liczba zderzen:\t\t', self.pomiary.N)

        czest = self.pomiary.N / self.czas
        print('Czestosc zderzen:\t', round(czest, 2))

        for i in range(len(self.pomiary.points) - 1):
            j = i + 1
            self.pomiary.droga += self.pomiary.points[i].distance_to(self.pomiary.points[j])
        print('Laczna droga:\t\t', round(self.pomiary.droga, 2))

        if self.pomiary.N != 0:
            self.pomiary.droga_sr = self.pomiary.droga / self.pomiary.N
            sredn = round(self.pomiary.droga_sr, 2)
            print('Srednia droga:\t\t', sredn)
        else:
            sredn = round(self.pomiary.droga_sr, 2)
            print('Srednia droga:\t\t', sredn)

        result = [sredn, czest]

        return result


class Atom:

    # UTWORZENIE ATOMU
    def __init__(self, sym):

        self.r = sym.R                          # promień do rysowania
        self.m = sym.M                          # masa
        self.position = pygame.Vector2()        # wektor położenia
        self.velocity = pygame.Vector2()        # wektor prędkości
        self.position.x, self.position.y = 0, 0
        self.velocity.x, self.velocity.y = 0, 0
        # liczniki pomagające sprawdzić, czy atom przed chwilą nie odbił się od bandy
        self.banda_poz = 0
        self.banda_pion = 0
        self.color = pygame.Color('blue')       # nadanie koloru

        # losowanie współrzędnych początkowych
        check = True
        while check:
            check = False
            # losowanie pozycji
            self.position.x = random.randint(0 + sym.R, sym.a - sym.R)
            self.position.y = random.randint(0 + sym.R, sym.a - sym.R)
            for i in sym.atoms:
                # jeśli pokrywa się z inną losuj ponownie
                if self.position.distance_to(i.position) < 2 * sym.R:
                    check = True
                    break

        self.velocity.x = random.randint(0, sym.v_range)
        self.velocity.y = random.randint(0, sym.v_range)
        if random.randint(0, 2) == 1:
            self.velocity.y = -self.velocity.y
        if random.randint(0, 2) == 1:
            self.velocity.x = -self.velocity.x

        return

    # RYSOWANIE ATOMU
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), self.r)
        return

    # ZMIANA POŁOŻENIA
    def move(self, sym):
        self.position += self.velocity * sym.tps
        return


# ----------------------------------------- M A I N -----------------------------------------

while True:

    print('\n-----------------------------------------------------------\n')
    print('\t S Y M U L A C J A \n')
    print('[A] - ustawienia automatyczne')
    print('[P] - prezentacja')
    print('[T] - testy')
    print('[Z] - zakończ')

    choice = input('\nWybierz działanie: ')
    choice = choice.lower()

    if choice == 'a':

        time = 30
        promien = 7
        N = 80
        ilosc = 80
        vel = 150

        print('\n-----------------------------------------------------------\n')
        print('\t P R Z E B I E G ')
        SYM = Symulacja(promien, N, vel, ilosc, time)
        SYM.inicjalizuj()
        SYM.run_sym()
        SYM.podsumowanie()

    elif choice == 'p':

        print('\n-----------------------------------------------------------\n')
        print('\t U S T A W I E N I A \n')
        print('Sugerowane ustawienia automatyczne:')
        print('- dlugosc promienia: \t7')
        print('- wymiary ekranu: \t\t560')
        print('- liczba atomów: \t\t80')
        print('- zakres predkosci: \t150')
        time = input('\nCzas trwania symulacji (w sekundach): ')
        time = int(time)
        promien = input('Dlugosc promienia atomu: ')
        promien = int(promien)
        wym = input('Wymiary ekranu: ')
        wym = int(wym)
        N = int(wym / promien)
        while N < 20:
            wym = input('Podaj wieksze wymiary ekranu: ')
            wym = int(wym)
            N = int(wym / promien)
        ilosc = input('Liczba atomow: ')
        ilosc = int(ilosc)
        while ilosc > N ** 2 * 0.25:
            ilosc = input('Mniejsza liczba atomow: ')
            ilosc = int(ilosc)
        vel = input('Zakres predkosci: ')
        vel = int(vel)

        print('\n-----------------------------------------------------------\n')
        print('\t P R Z E B I E G ')
        SYM = Symulacja(promien, N, vel, ilosc, time)
        SYM.inicjalizuj()
        SYM.run_sym()
        SYM.podsumowanie()

    elif choice == 't':

        promien = 7
        vel = 150
        N = 80
        timing = [10, 20, 30, 40, 50, 60]
        number = [75, 100, 125, 150, 175, 200, 225, 250, 275, 300]
        testy = open('testy.txt', 'a')

        for m in timing:
            time = m

            for n in number:
                ilosc = n

                for x in range(10):
                    print('\n-----------------------------------------------------------\n')
                    print('\t P R Z E B I E G ')
                    SYM = Symulacja(promien, N, vel, ilosc, time)
                    SYM.inicjalizuj()
                    SYM.run_sym()
                    res = SYM.podsumowanie()
                    srednia = res[0]
                    czestosc = res[1]
                    text = str(m) + ' ' + str(n) + ' ' + str(srednia) + ' ' + str(czestosc) + '\n'
                    print('\n', text, '\n')
                    testy.write(text)

        testy.close()
        break

    elif choice == 'z':

        print('\n-----------------------------------------------------------\n')
        print('Dziekujemy za skorzystanie z naszego programu.'
              '\nZa wszelkie wady zwiazane z jego dzialaniem serdecznie przepraszamy.'
              '\nDo widzenia.')
        print('\n-----------------------------------------------------------\n')

        break
