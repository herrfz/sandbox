BANNER = r'''
This script calculates the default channel hopping sequence for the
IEEE802.15.4e-2012 TSCH mode.

\author Thomas Watteyne
\date November 2014
\license http://opensource.org/licenses/BSD-3-Clause
'''

class Lfsr(object):
    '''
    \brief Pure Python implementation of a Linear feedback shift register, see
    http://en.wikipedia.org/wiki/Linear_feedback_shift_register.
    '''
    
    def __init__(self,numbits,taps,seed):
        
        # store params
        self.numbits    = numbits
        self.taps       = sorted(taps)
        self.seed       = seed
        
        # local variables
        self.shiftreg   = self.int2reg(self.seed)
    
    #==== lfsr
    
    def iter(self):
        
        # calculate value of the carrybit
        carrybit = self.shiftreg[-1]
        for tap in sorted(self.taps,reverse=True):
            if tap==self.numbits:
                continue
            carrybit ^= self.shiftreg[tap-1]
        
        # shift the register
        self.shiftreg  = self.shiftreg[:-1]
        self.shiftreg.insert(0,carrybit)
    
    #=== formatting
    
    def formatHeader(self):
        returnVal  = []
        for i in [b+1 for b in range(self.numbits)]:
            if i in self.taps:
                returnVal += [str(i)]
            else:
                returnVal += [' ']
        returnVal  = '   '+' '.join(returnVal)
        return returnVal
    
    def formatReg(self):
        returnVal  = []
        returnVal += ['   ']
        returnVal += [' '.join([str(b) for b in self.shiftreg])]
        returnVal += [' ({0:>4}==0x{0:03x}==b{0:09b})'.format(self.reg2int())]
        returnVal  = ''.join(returnVal)
        return returnVal
    
    #==== converters
    
    def int2reg(self,intNum):
        returnVal  = [0]*self.numbits
        for i in range(self.numbits):
            if intNum & (1<<i):
                returnVal[i]=1
        return returnVal
    
    def reg2int(self):
        returnVal = 0
        for i in range(self.numbits):
            returnVal += self.shiftreg[i]<<i
        return returnVal
    
if __name__=="__main__":
    
    NUMCHANS = 16
    
    print(BANNER)
    
    #======
    
    print('\n=== Step a.\n\nSHUFFLE is a macHoppingSequenceLength-sized array. The contents of this array are equivalent to the first macHoppingSequenceLength outputs of a 9-bit linear feedback shift register (LFSR) with polynomial x9 + x5 + 1 and a starting seed of 255. Each LFSR output is modulo macHoppingSequenceLength, so that each entry of SHUFFLE is between 0 and (macHoppingSequenceLength - 1), inclusive.\n')
    
    lfsr = Lfsr(
        numbits = 9,
        taps    = [5,9],
        seed    = 255,
    )
    
    print(lfsr.formatHeader())
    print(lfsr.formatReg())
    
    var_SHUFFLE = []
    for c in range(NUMCHANS):
        lfsr.iter()
        var_SHUFFLE += [lfsr.reg2int()%NUMCHANS]
        print('{0} --> {1}'.format(lfsr.formatReg(),var_SHUFFLE[-1]))
    
    print('\nSHUFFLE:  {0}'.format(var_SHUFFLE))
    
    #======
    
    print('\n=== Step b.\n\nCHANNELS is a macHoppingSequenceLength-sized array that is initially populated with the monotonically increasing list of channels available to the PHY.\n')
    
    var_CHANNELS = range(NUMCHANS)
    
    print('CHANNELS: {0}'.format(var_CHANNELS))
    
    #======
    
    print('\n=== Step c.\n\nCHANNELS is shuffled as per Figure 7a. Elements may wind up being swapped multiple times in this process.\n')
    
    for i in range(NUMCHANS):
       chan_i                          = var_CHANNELS[i]
       chan_shuffle_i                  = var_CHANNELS[var_SHUFFLE[i]]
       
       var_CHANNELS[i]                 = chan_shuffle_i
       var_CHANNELS[var_SHUFFLE[i]]    = chan_i
    
    print('macHoppingSequenceList: {0}'.format(var_CHANNELS))
    
    raw_input('\n\nScript ended normally, press Enter to close.')

