from lingpy.align.pairwise import pw_align

a = "Das Restaurant sollte sehr gutes Essen haben."
b = "Das Restaurant sollte sehr gut Essen haben."

#enthält Alignment auf String-Ebene
alignment = pw_align(a, b)

print(alignment[0])
print(alignment[1])


#Beispiel, wie man aus dem String Alignment die sich entsprechenden Wörter erhalten kann:
word_a = ""
word_b = ""

aligned = []

#Iteriere über alle Characters
for i in range(len(alignment[0])):
    char_a = alignment[0][i]
    char_b = alignment[1][i]

    #Bis ein Leerzeichen kommt, Buchstaben an das aktuelle Wort anfügen
    if char_a != " " and char_b != " ":
        if char_a != "-": # "-" steht für leeren String: ignorieren
            word_a += char_a
        if char_b != "-":
            word_b += char_b

    # wennn in beiden Strings ein Leerzeichen oder am Ende des Strings angelangt: Wort zuende
    if (char_a == char_b and char_a == " ") or i == len(alignment[0])-1:

        #an Alignment-Liste als Tupel anfügen
        aligned.append((word_a, word_b))

        #aktuelles Wort "leeren" für das nächste Wort
        word_a = ""
        word_b  = ""

# Wortpaare ausgeben
for (a, b) in aligned:
    print(a, b)
    