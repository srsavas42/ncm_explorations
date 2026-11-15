"""Draw the verified four-arm fixture; annotation is never used as model input."""
import argparse
import json
from pathlib import Path
from ncm_probe.analysis import pyplot
from ncm_probe.sudoku import parse,eligible
from ncm_probe.opposite_puzzles import ARMS,validate

def draw(root):
    plt = pyplot()
    from matplotlib.patches import Rectangle
    f = json.loads((root/'ncm_probe/fixtures/opposite-engineering.json').read_text())
    validate(f)
    p,q = f['locations']
    d,e = f['digit'],f['rival']
    fig,axes = plt.subplots(2,2,figsize=(10,12))
    for ax,arm in zip(axes.flat,ARMS):
        board = parse(f['boards'][arm])
        forced = p if arm.endswith('_P') else q
        locations = eligible(board,forced,d)[2]
        label = 'Box rule' if arm.startswith('rule') else 'Remote control'
        orientation = 'P' if forced == p else 'Q'
        ax.set_title(f'{label} → {orientation}\nBox locations for {d}: '+
                     ', '.join('P' if i == p else 'Q' for i in locations),fontsize=12,pad=12)
        ax.set(xlim=(-.1,9.1),ylim=(9.1,-.1),aspect='equal')
        ax.axis('off')
        br,bc = (p//27)*3,((p%9)//3)*3
        ax.add_patch(Rectangle((bc,br),3,3,facecolor='#eef3f8',edgecolor='none'))
        endpoint = f['endpoints'][arm]
        er,ec = divmod(endpoint,9)
        ax.add_patch(Rectangle((ec,er),1,1,facecolor='#eadcf9',edgecolor='none'))
        for cell,letter,color in ((p,'P','#1976b7'),(q,'Q','#cf7000')):
            r,c = divmod(cell,9)
            ax.add_patch(Rectangle((c+.08,r+.08),.84,.84,facecolor='white',edgecolor=color,linewidth=2))
            ax.text(c+.5,r+.53,letter,ha='center',va='center',color=color,fontsize=14,fontweight='bold')
        for i,value in enumerate(board):
            if value:
                r,c = divmod(i,9)
                ax.text(c+.5,r+.53,str(value),ha='center',va='center',fontsize=14,
                        color='#6c2e92' if i == endpoint else '#232b34',
                        fontweight='bold' if i == endpoint else 'normal')
        for k in range(10):
            width = 1.8 if k%3 == 0 else .45
            ax.plot([0,9],[k,k],color='#34404a',linewidth=width)
            ax.plot([k,k],[0,9],color='#34404a',linewidth=width)
    fig.suptitle(f'Opposite-answer fixture · {d} and {e} exchange locations\nFour 35-clue puzzles; two different unique solutions',fontsize=15,y=.98)
    fig.text(.5,.025,'P/Q mark blank cells. Purple highlights the one added clue.\n'
             'Rule/control arms with the same letter share a solution; opposite letters require opposite assignments.',
             ha='center',fontsize=10)
    fig.subplots_adjust(top=.84,bottom=.09,left=.04,right=.96,wspace=.15,hspace=.45)
    output = root/'outputs/opposite-v1/fixture'
    output.mkdir(parents=True,exist_ok=True)
    fig.savefig(output/'opposite-boards.png',dpi=170)
    fig.savefig(output/'opposite-boards.svg')
    plt.close(fig)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    draw(parser.parse_args().root.resolve())
