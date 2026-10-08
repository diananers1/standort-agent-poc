/** Decorative architectural line art, kept out of the accessibility tree. */
export function CitySkyline() {
  const buildings = [
    { x: 25, width: 64, height: 68 }, { x: 100, width: 54, height: 92 },
    { x: 166, width: 76, height: 56 }, { x: 256, width: 66, height: 136 },
    { x: 337, width: 44, height: 174 }, { x: 396, width: 82, height: 86 },
    { x: 492, width: 70, height: 114 }, { x: 579, width: 57, height: 70 },
    { x: 650, width: 75, height: 156 }, { x: 741, width: 64, height: 208 },
    { x: 821, width: 57, height: 127 }, { x: 893, width: 85, height: 77 },
    { x: 992, width: 70, height: 164 }, { x: 1077, width: 54, height: 103 },
    { x: 1148, width: 75, height: 59 }, { x: 1240, width: 60, height: 119 },
    { x: 1315, width: 62, height: 82 },
  ];
  return <div className="city-skyline" aria-hidden="true"><svg viewBox="0 0 1400 230" fill="none" focusable="false">
    <g stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M0 230H1400" opacity=".65"/>
      {buildings.map(({x,width,height},index) => {
        const top = 230-height;
        return <g key={x} opacity={index % 3 === 0 ? '.8' : '.5'}>
          <path d={`M${x} 230V${top}H${x+width}V230`}/>
          {height > 130 && <path d={`M${x+width*.25} ${top}V${top-9}H${x+width*.75}V${top}M${x+width/2} ${top-9}V${top-23}`}/>}
          {Array.from({length:Math.floor((height-20)/18)},(_,row)=><path key={row} d={`M${x+11} ${top+16+row*18}H${x+width-11}`} opacity=".45"/>)}
          <path d={`M${x+width/2} ${top+12}V220`} opacity=".35"/>
          <path d={`M${x+width/2-6} 230V217H${x+width/2+6}V230`} opacity=".7"/>
        </g>;
      })}
      {[145,385,570,885,1137,1308].map(x=><g key={x} opacity=".65"><path d={`M${x} 230V215M${x-8} 230H${x+8}`}/><circle cx={x} cy="205" r="10"/></g>)}
    </g>
  </svg></div>;
}
