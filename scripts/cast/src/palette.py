"""Character materials.  Four tones each: deep, shadow, base, light (plus an optional shine).
Shadows lean cool (toward violet), lights lean warm (toward yellow), like the world ramps in
art/materials.json; the outline of each material is its deep tone pulled 62% to the ink."""
from ew import mat

# people
mat('skin',    ['#7A3E3A', '#B8705A', '#E3A27C', '#F7CDA2'])
mat('skin_d',  ['#5A2E2E', '#8E5040', '#B8785A', '#D69C74'])          # (spare: darker skin)
mat('blush',   ['#A9505A', '#C86A66', '#E08A7A', '#F0A890'])
mat('eye',     ['#1E1917', '#1E1917', '#2A2230', '#FFFDF5'])
# Bramble
mat('grey',    ['#4C4858', '#7C7884', '#ABA8A8', '#DCD8CC'])
mat('mantle',  ['#1E3A30', '#2E5E3C', '#4B8A3E', '#7DB050'])
mat('cream',   ['#7C6E6E', '#B6A38A', '#DDD0AE', '#F5EDD6'])
mat('leather', ['#3A2522', '#5E3C2E', '#80573A', '#A6784E'])
mat('trouser', ['#45343A', '#6C5348', '#93715A', '#B49274'])
mat('gold',    ['#6E4A1E', '#A8782E', '#E0B24E', '#F8DD8F', '#FFF4C8'])
mat('bow',     ['#57301E', '#8A4C26', '#BA7432', '#DE9E4E'])
mat('steel',   ['#3A3F4E', '#656C7E', '#9AA2B0', '#D6DAE0', '#FFFFFF'])
mat('fletch',  ['#86808F', '#B7B2BA', '#E4E0DA', '#FFFDF5'])
mat('string',  ['#B7B2BA', '#B7B2BA', '#E4E0DA', '#FFFDF5'])
# Iona
mat('berry',   ['#4A1830', '#7E1E40', '#B82A4E', '#E4506A'])
mat('scarf',   ['#5A1236', '#9A1A4E', '#D8285E', '#F65E80'])
mat('taupe',   ['#4E4652', '#786E74', '#A39890', '#C9BEB0'])
mat('braid',   ['#1C1236', '#2E1A54', '#47287A', '#6A44A4'])
mat('violet',  ['#2A1E46', '#43306A', '#5E4890', '#8068B4'])
mat('storm',   ['#283A86', '#3C78D4', '#78CCFF', '#DDF6FF', '#FFFFFF'])
mat('brownb',  ['#3E2620', '#6A4030', '#94603E', '#B8865A'])
# Pendle
mat('duster',  ['#3A1E1A', '#5E3426', '#86502E', '#AA6E40'])
mat('hat',     ['#22101A', '#52302A', '#86523A', '#C48658'])
mat('brass',   ['#4E3014', '#86561E', '#C08A30', '#ECC060', '#FFEDB0'])
mat('robo',    ['#1A1A26', '#2A2C3C', '#3E4256', '#5A6078', '#8890A8'])
mat('bandana', ['#5A1A2E', '#8E2440', '#C83A58', '#EE6A7C'])
mat('glow',    ['#B86A10', '#F0A020', '#FFD24A', '#FFF4B0'])
mat('gunmetal',['#1E2028', '#343846', '#525868', '#7A8292', '#C0C6D0'])
mat('rifle',   ['#4A2614', '#7E4220', '#B4682C', '#E09A4C'])   # walnut, lighter than the duster
# Cairn
mat('granite', ['#5A5060', '#8E8590', '#BDB4AE', '#E2DACB', '#F4EEE2'])
mat('moss',    ['#1E3826', '#2E5A2C', '#4C8A32', '#7CB642', '#A8CC66'])
mat('crack',   ['#241E2A', '#2E2834', '#3A3440', '#4A4452'])
mat('amber',   ['#8A4A10', '#E08A20', '#FFC040', '#FFF0A0'])
# Briarshot growth (Bramble) and shared accents
mat('leafg',   ['#1E3A22', '#2E6A2C', '#52A03A', '#8CCB52'])
mat('bloom',   ['#7A2A4A', '#B84A6A', '#E07A92', '#FFC2CC'])
