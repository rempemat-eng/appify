"""python3 export.py <id> [clip,clip] [--facings 8]: render every clip to out/<id>/ (anim.export).
The shipped contract has four body facings; --facings 8 renders the stored three-quarter facings too."""
import sys
import importlib
import anim
args = [a for a in sys.argv[1:] if not a.startswith('--')]
eight = '--facings' in sys.argv and sys.argv[sys.argv.index('--facings') + 1] == '8'
if eight:
    args = [a for a in args if a != '8']
cid = args[0]
clips = args[1].split(',') if len(args) > 1 else None
mod = importlib.import_module(cid)
A = importlib.import_module('anim_' + cid)
if __name__ == '__main__':
    anim.export(mod, A, clips=clips, facings=anim.FACINGS8 if eight else None)
