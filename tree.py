class node(object):
    def __init__(self,name='root'):
        self.children = [False]
        self.name = name
        
root = node()
hip = node('hip')
rUpleg = node('rUpleg')
rLoleg = node('rLoleg')
rFoot = node('rFoot')
lUpleg = node('lUpleg')
lLoleg = node('lLoleg')
lFoot = node('lFoot')
mWaist = node('mWaist')
mUpbody = node('mUpbody')
mShldrs = node('mShldrs')
mNeck = node('mNeck')
mHead = node('mHead')
rUparm = node('rUparm')
rLoarm = node('rLoarm')
rhand = node('rhand')
lUparm = node('LUparm')
lLoarm = node('LLoarm')
lhand = node('Lhand')

root.children = [hip]
hip.children = [rUpleg, lUpleg, mWaist]
rUpleg.children = [rLoleg]
rLoleg.children = [rFoot]
lUpleg.children = [lLoleg]
lLoleg.children = [lFoot]
mWaist.children = [mUpbody]
mUpbody.children = [mShldrs]
mShldrs.children = [mNeck]
mNeck.children = [mHead]
rUparm.children = [rLoarm]
rLoarm.children = [lUparm]
lUparm.children = [lLoarm]
lLoarm.children = [lhand]


def walk (node):
    for i in node.children:
        if i:
            print i.name
            walk(i)


walk(root)
