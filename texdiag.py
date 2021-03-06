import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os.path


def diagnose(fname, plot_gantt=True, showfigures=True, showincluded=True, showlist=True, showempty=True):

    if not fname.endswith('.tex'):
        print('Please pass a .tex file.')
        return 0
    if not os.path.isfile(fname):
        print('No such file')
        return 0
    print('Diagnosing...(may take several minutes)')
    path = '/'.join(fname.split('/')[0:-1])+'/'

    file = open(fname, "r")
    words = []
    included = []
    for word in file.read().split():
        if word.startswith('%'):
            continue
        if '\include' in word:
            i = word.split('{')[1]
            i = i.split('}')[0]
            included = np.append(included, i)
            for w in open(path+i+'.tex').read().split():
                words = np.append(words, w)
        words = np.append(words, word)
    file.close()
    f = open('texdiag.txt', 'w')
    if showincluded == True:
        f.write('-----------------------------------------\nINCLUDED TEX FILES\n')
        f.write('=================\n')
        for i in included:
            f.write('{}\n'.format(i))

    types = ['\part', '\chapter', '\section', '\subsection',
             '\subsubsection', '\paragraph', '\subparagraph']
    aims = [10000, 5000, 1000, 500, 300, 150, 100]
    w = '\section{Introduction}'
    seccount = 0
    for i, w in enumerate(words):
        pos = [t in w for t in types]
        contained = np.any(pos)
        if contained:
            test = ' '.join(words[i:i+100])
            try:
                heading = test[test.index('{')+1:test.index('}')]
            except:
                heading = w
            if heading.startswith("\\"):
                continue
            seccount += 1
    secs = np.empty((len(types), seccount), dtype='U64')
    for s in range(len(types)):
        for x in range(seccount):
            secs[s, x] = '-'

    wcounts = np.zeros((len(types), seccount))
    read = 0
    sec = 0
    wordcount = 0
    prevlevel = 0
    for i, w in enumerate(words):
        pos = [t in w for t in types]
        contained = np.any(pos)
        pos = np.where(np.asarray(pos) == True)[0]
        if contained:
            level = pos
            test = ' '.join(words[i:i+100])
            try:
                heading = test[test.index('{')+1:test.index('}')]
            except:
                heading = w
            if heading.startswith("\\"):
                continue
            secs[level, sec] = heading
            if sec-1 >= 0:
                wcounts[prevlevel, sec-1] = wordcount
            wordcount = 0
            sec += 1
            prevlevel = pos
        wordcount += 1
    wcounts[prevlevel, sec-1] = wordcount
    if showfigures == True:
        f.write('-----------------------------------------\nINCLUDED FIGURES FILES\n')
        f.write('=================\n')
        for w in words:
            if ('\includegraphics' in w) or ('\plotone' in w):
                f.write('{}\n'.format(w[w.index('{')+1:w.index('}')]))

    headings = np.empty(len(np.transpose(secs)), dtype='U64')
    wc = np.zeros(len(np.transpose(secs)))
    level = np.zeros(len(np.transpose(secs)))
    for i, s, w in zip(range(len(np.transpose(secs))), np.transpose(secs), np.transpose(wcounts)):
        try:
            headings[i] = s[np.where(s != '-')][0]
            wc[i] = w[np.where(s != '-')][0]
            level[i] = np.where(s != '-')[0]
        except:
            continue

    stacked = np.zeros(len(np.transpose(secs)))
    for i in range(len(wc)):
        j = 1
        while i+j < len(wc):
            if level[i+j] <= level[i]:
                break
            j += 1
        stacked[i] = np.sum(wc[i:i+j])

    x = np.arange(len(wc))
    bottom = np.zeros(len(level))
    top = np.zeros(len(level))
    top[0] = stacked[0]

    for i, l in enumerate(level):
        if i == 0:
            continue
        bottom[i] = top[i-1]
        top[i] = top[i-1]+stacked[i]
        if level[i]-level[i-1] > 0:
            bottom[i] -= stacked[i-1]
            top[i] -= stacked[i-1]
            bottom[i] += wc[i-1]
            top[i] += wc[i-1]

    if plot_gantt == True:
        ysize = 0.25*len(wc)
        if ysize < 10:
            ysize = 10
        plt.figure(figsize=(10, ysize))
        plt.barh(x, top, align='center')
        plt.xlabel('Word Count')
        for i in range(len(wc)):
            color = 'blue'
            if stacked[i] >= aims[int(level[i])]*0.5:
                color = 'limegreen'
            if stacked[i] <= aims[int(level[i])]*0.5:
                color = 'orange'
            if stacked[i] <= aims[int(level[i])]*0.1:
                color = 'red'

            plt.barh(x[i], top[i], align='center', color=color, edgecolor='white')

        plt.barh(x, bottom, color='white', edgecolor='white', align='center')
        for i in range(len(wc)):
            if stacked[i] < 10:
                color = 'red'
                plt.barh(x[i], np.max(top), align='center',
                         color=color, edgecolor='white', alpha=0.3)

        plt.ylim(len(wc)+1, -1)
        plt.yticks(x, headings)
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='Short Section')
        orange_patch = mpatches.Patch(color='orange', label='Middling Section')
        green_patch = mpatches.Patch(color='limegreen', label='Acceptable Section')
        red2_patch = mpatches.Patch(color='red', label='Missing Section', alpha=0.3)
        plt.legend(handles=[red_patch, orange_patch, green_patch, red2_patch], loc='best')
        plt.savefig('texdiag.png', bbox_inches='tight')
        plt.cla()
        plt.clf()

    if showlist == True:
        f.write('-----------------------------------------\nINCLUDED SECTION LIST\n')
        f.write('=================\n')
        for l, h, st in zip(level, headings, stacked):
            try:
                abrv = h[0:40]
            except:
                abrv = h
            f.write('{}{}{}\n'.format('-'.join(['------------'] *
                                               np.int(l)), abrv, ' (', np.int(st), ' words)'))

    if showempty == True:
        f.write('-----------------------------------------\nEMPTY SECTIONS LIST\n')
        f.write('=================\n')
        for l, h, w in zip(level, headings, wc):
            if w < 20:
                f.write('{}{}\n'.format('Empty '+types[np.int(l)][1:]+': ', h))

    f.write('-----------------------------------------\n')
    f.write('Total Words: {}\n'.format(np.sum(wc)))
    if plot_gantt == True:
        f.write('Gantt Diagram plotted to texdiag.pdf\n')
    f.write('-----------------------------------------\n')
    f.close()


if __name__ == "__main__":
    diagnose(sys.argv[1])
