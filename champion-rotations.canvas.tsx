import { useHostTheme, useState } from "cursor/canvas";

const panels = [{"team":"San Antonio Spurs","year":2007,"league":"NBA","field":16,"main":[["Facilitator",7.48,7.32],["High-volume shooter",7.35,7.35],["Interior player",-0.0,0.0],["Passing big",8.17,8.17],["Perimeter shooter",20.6,20.23],["Primary facilitator",-6.9,-6.9],["Rebound specialist",-15.62,-15.62],["Rebounder",-5.41,-5.76],["Scorer",-1.51,-1.98],["Secondary facilitator",-6.54,-6.54],["Shot blocker",-7.79,-7.6],["Stretch big",0.17,0.17]],"earned":[["High-volume shooter",15.5],["Passing big",3.76],["Primary facilitator",-9.28],["Rebound specialist",0.45],["Secondary facilitator",-7.59],["Shot blocker",7.01],["Stretch big",-1.01],["Stretch five",1.86]]},{"team":"San Antonio Spurs","year":2007,"league":"NBA","field":8,"main":[["Facilitator",8.51,8.29],["High-volume shooter",9.22,9.22],["Interior player",-0.0,0.0],["Passing big",10.1,10.1],["Perimeter shooter",24.1,23.8],["Primary facilitator",-7.92,-7.92],["Rebound specialist",-19.53,-19.53],["Rebounder",-1.54,-1.97],["Scorer",-6.1,-6.59],["Secondary facilitator",-4.55,-4.55],["Shot blocker",-12.68,-12.55],["Stretch big",0.4,0.4]],"earned":[["High-volume shooter",16.42],["Passing big",3.12],["Primary facilitator",-11.64],["Rebound specialist",-5.11],["Secondary facilitator",-6.78],["Shot blocker",5.24],["Stretch big",-0.08],["Stretch five",1.38]]},{"team":"Florida Gators","year":2007,"league":"NCAA","field":16,"main":[["Facilitator",9.24,10.33],["High-volume shooter",3.54,3.54],["Interior player",0.0,0.0],["Passing big",21.03,21.03],["Perimeter player",-0.02,0.0],["Perimeter shooter",-4.19,-4.41],["Primary facilitator",-10.03,-10.03],["Rebound specialist",2.55,2.55],["Rebounder",-4.08,-3.37],["Scorer",12.86,12.97],["Secondary facilitator",-7.81,-7.81],["Shot blocker",-23.1,-23.75]],"earned":[["High-volume shooter",0.29],["Passing big",32.22],["Primary facilitator",-12.08],["Rebound specialist",5.45],["Secondary facilitator",-8.24],["Shot blocker",1.8],["Stretch big",-2.9]]},{"team":"Florida Gators","year":2007,"league":"NCAA","field":8,"main":[["Facilitator",8.04,9.42],["High-volume shooter",4.86,4.86],["Interior player",0.0,0.0],["Passing big",18.27,18.27],["Perimeter player",0.0,0.0],["Perimeter shooter",-5.42,-5.69],["Primary facilitator",-8.16,-8.16],["Rebound specialist",0.4,0.4],["Rebounder",-2.89,-2.57],["Scorer",15.25,15.37],["Secondary facilitator",-6.76,-6.76],["Shot blocker",-23.59,-24.22]],"earned":[["High-volume shooter",3.88],["Passing big",31.01],["Primary facilitator",-10.11],["Rebound specialist",1.18],["Secondary facilitator",-7.69],["Shot blocker",-6.49],["Stretch big",-6.2]]},{"team":"New York Knicks","year":2026,"league":"NBA","field":16,"main":[["Facilitator",-3.0,-3.02],["High-volume shooter",-0.94,-0.94],["Interior player",0.0,0.0],["Passing big",-6.85,-6.85],["Perimeter player",0.0,0.0],["Perimeter shooter",-9.79,-10.25],["Primary facilitator",9.21,9.21],["Rebound specialist",19.2,19.2],["Rebounder",-5.83,-6.52],["Scorer",-3.46,-3.37],["Secondary facilitator",-1.04,-1.04],["Shot blocker",2.17,2.67],["Stretch big",0.34,0.34]],"earned":[["High-volume shooter",-3.9],["Passing big",-7.42],["Primary facilitator",7.67],["Rebound specialist",11.87],["Secondary facilitator",-1.99],["Shot blocker",-5.39],["Stretch big",-0.29],["Stretch five",-1.46]]},{"team":"New York Knicks","year":2026,"league":"NBA","field":8,"main":[["Facilitator",-2.47,-2.45],["High-volume shooter",-1.66,-1.66],["Interior player",0.0,0.0],["Passing big",-6.77,-6.77],["Perimeter player",0.0,0.0],["Perimeter shooter",-6.45,-6.97],["Primary facilitator",10.07,10.07],["Rebound specialist",22.02,22.02],["Rebounder",-4.97,-5.69],["Scorer",-3.86,-3.66],["Secondary facilitator",-0.16,-0.16],["Shot blocker",-5.7,-5.11],["Stretch big",-0.04,-0.04]],"earned":[["High-volume shooter",-5.32],["Passing big",-7.69],["Primary facilitator",6.78],["Rebound specialist",10.91],["Secondary facilitator",-0.69],["Shot blocker",-6.38],["Stretch big",-1.39],["Stretch five",-2.33]]},{"team":"Michigan Wolverines","year":2026,"league":"NCAA","field":16,"main":[["Facilitator",-4.26,-4.63],["High-volume shooter",9.85,9.85],["Interior player",0.0,0.0],["Passing big",9.84,9.84],["Perimeter player",-0.02,0.0],["Perimeter shooter",-5.03,-5.65],["Primary facilitator",-2.52,-2.52],["Rebound specialist",-1.37,-1.37],["Rebounder",-0.65,-0.88],["Scorer",-3.78,-3.56],["Secondary facilitator",2.51,2.51],["Shot blocker",-7.98,-7.35],["Stretch big",3.4,3.4]],"earned":[["High-volume shooter",6.6],["Passing big",9.22],["Primary facilitator",-2.52],["Rebound specialist",12.98],["Secondary facilitator",2.51],["Shot blocker",4.27],["Stretch big",14.67]]},{"team":"Michigan Wolverines","year":2026,"league":"NCAA","field":8,"main":[["Facilitator",-6.87,-6.9],["High-volume shooter",13.16,13.16],["Interior player",0.0,0.0],["Passing big",4.94,4.94],["Perimeter player",-0.03,0.0],["Perimeter shooter",-6.17,-6.88],["Primary facilitator",-1.02,-1.02],["Rebound specialist",-2.03,-2.03],["Rebounder",-0.18,-0.56],["Scorer",-1.27,-1.07],["Secondary facilitator",0.41,0.41],["Shot blocker",-3.43,-2.97],["Stretch big",2.49,2.49]],"earned":[["High-volume shooter",11.62],["Passing big",3.61],["Primary facilitator",-1.02],["Rebound specialist",8.44],["Secondary facilitator",0.41],["Shot blocker",4.49],["Stretch big",13.15]]}];

export default function ChampionRotations() {
  const { palette } = useHostTheme();
  const [field, setField] = useState(16);
  const [view, setView] = useState("main");
  const current = panels.filter(panel => panel.field === field);
  const max = Math.ceil(Math.max(...panels.flatMap(panel =>
    [...panel.main, ...panel.earned].flatMap(row => row.slice(1).map(value => Math.abs(Number(value))))
  )) / 10) * 10;
  const x = (value: number) => 50 + 50 * value / max;
  const number = (value: number) => `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
  const control = {
    color: palette.foreground, background: palette.elevated,
    border: `1px solid ${palette.strokePrimary}`, padding: "6px 8px", borderRadius: 4,
  };

  return <main style={{ padding: 20, color: palette.foreground, fontFamily: "Inter, sans-serif" }}>
    <h1 style={{ fontSize: 24, margin: "0 0 6px" }}>How champions used their rotations</h1>
    <p style={{ color: palette.foregroundSecondary, margin: "0 0 16px" }}>
      Difference in pre-postseason minutes share between each champion and the average of the other teams.
    </p>
    <div style={{ display: "flex", flexWrap: "wrap", gap: 16, fontSize: 13 }}>
      <label>Comparison field{" "}
        <select style={control} value={field} onChange={event => setField(Number(event.target.value))}>
          <option value={16}>All 16 teams</option>
          <option value={8}>Final eight</option>
        </select>
      </label>
      <label>Role view{" "}
        <select style={control} value={view} onChange={event => setView(event.target.value)}>
          <option value="main">Main roles</option>
          <option value="earned">All earned roles</option>
        </select>
      </label>
    </div>
    <p style={{ fontSize: 12, color: palette.foregroundSecondary }}>
      {view === "main"
        ? "Bars show all assigned main roles. Diamonds show the result after grouping low-confidence assignments as uncertain."
        : "Includes every role that met its statistical thresholds. A player's minutes can count toward multiple roles."}
    </p>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 450px), 1fr))", gap: 24 }}>
      {current.map(panel => {
        const rows = [...(view === "main" ? panel.main : panel.earned)].sort((a, b) => Number(b[1]) - Number(a[1]));
        return <section key={panel.team} style={{ borderTop: `1px solid ${palette.strokePrimary}`, paddingTop: 10 }}>
          <h2 style={{ fontSize: 17, margin: "0 0 4px" }}>{panel.team}</h2>
          <div style={{ color: palette.foregroundSecondary, fontSize: 12, marginBottom: 10 }}>
            {panel.league} · {panel.year - 1}–{String(panel.year).slice(-2)} · Champion vs. {field - 1} teams
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "minmax(105px, 36%) 1fr 48px", gap: "4px 8px", alignItems: "center", fontSize: 12 }}>
            <span>Archetype</span>
            <div style={{ display: "flex", justifyContent: "space-between", color: palette.foregroundSecondary }}>
              <span>−{max}</span><span>0</span><span>+{max}</span>
            </div>
            <span>pp</span>
            {rows.map(([role, raw, checked]) => {
              const value = Number(raw);
              const stricter = typeof checked === "number" ? checked : null;
              return <div key={String(role)} style={{ display: "contents" }}>
                <span>{role}</span>
                <div title={`${role}: ${number(value)} pp${stricter === null ? "" : ` · confidence check ${number(stricter)} pp`}`}
                  style={{ position: "relative", height: 18, background: palette.fillQuaternary }}>
                  <span style={{ position: "absolute", left: "50%", height: "100%", width: 1, background: palette.strokePrimary }} />
                  <span style={{ position: "absolute", left: `${Math.min(50, x(value))}%`, width: `${Math.abs(x(value) - 50)}%`,
                    top: 4, bottom: 4, background: value >= 0 ? palette.accent : palette.foregroundTertiary }} />
                  {stricter !== null && <span style={{ position: "absolute", left: `${x(stricter)}%`, top: 5,
                    width: 7, height: 7, transform: "translateX(-50%) rotate(45deg)",
                    background: palette.foreground, border: `1px solid ${palette.editor}` }} />}
                </div>
                <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{number(value)}</span>
              </div>;
            })}
          </div>
        </section>;
      })}
    </div>
    <p style={{ fontSize: 12, color: palette.foregroundSecondary, marginTop: 18 }}>
      Source · Basketball Archetype Project pilot CSVs, 2006–07 and 2025–26. Differences are in percentage points (pp). Positional benchmarks are provisional.
    </p>
  </main>;
}
