const logarithms = new Map([[1,0n],[2,2977044471n],[3,4718503850n],[4,5954088943n]]);
export function aggregate(levels) {
  let result = 0n;
  for (const level of levels) {
    if (!Number.isInteger(level) || !logarithms.has(level)) throw new Error('Positive warrant 1..4 required');
    const term = logarithms.get(level);
    if (result > 9223372036854775807n - term) throw new Error('Signed Q32.32 accumulator exceeded');
    result += term;
  }
  return result;
}
if (process.argv[2]) console.log(aggregate(JSON.parse(process.argv[2])).toString());
