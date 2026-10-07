"""Compare all Chapter 5 experiments, retaining the earlier V1 campaigns."""
import hashlib
import json
from pathlib import Path
import re
import statistics

BASE = Path('results')
OUT = BASE / 'chapter5'
REFERENCE = {
    'simple': {'V1': [2.03, 1.0, 7, 5.19], 'V2': [1.85, 1.0, 7, 4.80],
               'V3': [2.53, 1.0, 9, 1.47], 'V4': [2.03, 1.0, 11, 1.66]},
    'A': {'V1': None, 'V2': {'energy': [15.79, .52], 'on_time': [.857, .030],
           'hubs': [4, 0], 'iterations': [8.9, 4.0], 'cpu': [2690.2, 1548.8]},
          'V3': None, 'V4': {'energy': [16.09, .60], 'on_time': [.879, .017],
           'hubs': [4, 0], 'iterations': [9.0, 5.2], 'cpu': [526.7, 340.8]}},
    'B': {'V1': {'energy': [15.06, .60], 'on_time': [1, 0], 'hubs': [4, 0],
                 'iterations': [7.8, 3.4], 'cpu': [2428.8, 1375.3]},
          'V2': {'energy': [14.79, .46], 'on_time': [1, 0], 'hubs': [4, 0],
                 'iterations': [8.2, 3.2], 'cpu': [2354.0, 1503.9]},
          'V3': {'energy': [15.50, .62], 'on_time': [1, 0], 'hubs': [4, 0],
                 'iterations': [7.4, 3.2], 'cpu': [347.4, 341.2]},
          'V4': {'energy': [15.70, .81], 'on_time': [1, 0], 'hubs': [4, 0],
                 'iterations': [8.8, 3.6], 'cpu': [373.6, 199.7]}},
}


def stats(values):
    return {'mean': statistics.mean(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0.0} if values else None


def fmt(value, digits=3):
    return f"{value['mean']:.{digits}f} ± {value['stdev']:.{digits}f}" if value else 'Không có nghiệm'


def main():
    entries = {}
    for scenario in ['simple', 'A', 'B']:
        for variant in ['V1', 'V2', 'V3', 'V4']:
            source = BASE / f'{scenario}.json' if variant == 'V1' else OUT / variant / f'{scenario}.json'
            report = json.loads(source.read_text(encoding='utf-8'))
            expected = 1 if scenario == 'simple' else 20
            if report.get('status') != 'completed' or len(report['runs']) != expected:
                raise SystemExit(f'Not complete: {scenario}/{variant}')
            runs = report['runs']
            # Older V1 JSON lacks CPU time; recover it from preserved stdout, not a new run.
            cpu_log = [float(v) for v in re.findall(r'Total algo time: ([0-9.eE+-]+)',
                        source.with_suffix('.log').read_text(encoding='utf-8'))]
            found = [r for r in runs if r['solution_found']]
            valid = [r for r in found if r['validation']['valid']]
            if len(valid) != len(found):
                raise SystemExit(f'Invalid schedule in {scenario}/{variant}')
            metrics = {
                'energy': stats([r['validation']['energy_j'] / 1e6 for r in valid]),
                'score': stats([r['validation']['score'] / 1e6 for r in valid]),
                'on_time': stats([r['validation']['on_time_fraction'] for r in valid]),
                'charging_visits': stats([r['validation']['charging_visits'] for r in valid]),
                'unique_hubs': stats([len({s['task'] for s in r['validation']['steps'] if s['charging']}) for r in valid]),
                'iterations': stats([r['iterations'] for r in valid]),
                'cpu': stats([r.get('cpu_time_s', cpu_log[r['run']-1]) for r in valid]),
                'wall': stats([r['wall_time_s'] for r in valid]),
            }
            key = f'{scenario}/{variant}'
            entries[key] = {'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                            'reused': variant == 'V1', 'runs': len(runs), 'solutions': len(found),
                            'valid_solutions': len(valid), 'campaign_wall_s': report['wall_time_s'],
                            'config': report['config'], 'metrics': metrics, 'reference': REFERENCE[scenario][variant]}
            if scenario == 'simple' and valid:
                routes = [[] for _ in range(valid[0]['uavs'])]
                for step in valid[0]['validation']['steps']:
                    routes[step['uav']].append(step['task'])
                entries[key]['routes'] = routes
    lines = [
        '# Đối chiếu Chương 5 — Simulation results', '',
        'Nguồn: luận văn Cristiano Bicchieri, Chương 5, trang in 30–35 (PDF trang 37–42).',
        'Dùng tài liệu người dùng cung cấp trong Downloads, SHA-256:',
        '`280610a51798064103d7b854bf89ad385c4496cbaf00b951afecd37a211640cd`.', '',
        '## Phần đã chạy và phần bổ sung', '',
        '- Giữ nguyên cả ba kết quả V1 lần trước, không chạy lại hay ghi đè file cũ.',
        '- Bổ sung simple/V2–V4: mỗi trường hợp 1 lần, tương ứng Bảng 5.2.',
        '- Bổ sung A/V2–V4 và B/V2–V4: mỗi trường hợp 20 lần Monte Carlo, tương ứng Bảng 5.3–5.4.',
        '- Tổng bổ sung: 9 trường hợp, 123 lượt GA; tổng cả kết quả cũ là 12 trường hợp, 164 lượt.', '',
        '| Phiên bản | Deadline | Thời điểm chèn sạc |',
        '|---|---|---|',
        '| V1 | Bắt buộc | Trong đánh giá từng thế hệ |',
        '| V2 | Mềm | Trong đánh giá từng thế hệ |',
        '| V3 | Bắt buộc | Sau khi tìm được nghiệm cuối |',
        '| V4 | Mềm | Sau khi tìm được nghiệm cuối |', '',
        '## Bảng 5.1 — Đặc tính đội UAV', '',
        '| UAV loại | m / tải trọng tối đa (kg) | Ar (m²) | Ad (m²) | vmax (m/s) | Emax (MJ) |',
        '|---|---:|---:|---:|---:|---:|',
        '| 0 | 1 / 1 | 0.20 | 0.4 | 16 | 0.68 |',
        '| 1 | 2 / 2 | 0.28 | 0.6 | 19 | 0.90 |',
        '| 2 | 3 / 3 | 0.36 | 0.8 | 20 | 1.17 |',
        '| 3 | 4 / 4 | 0.44 | 1.0 | 22 | 1.43 |',
        'Simple dùng UAV loại 1 và 3; complex dùng đủ 4 loại. Đã kiểm tra bằng cách đọc input',
        'của các script, không chạy lại GA; xem `inputs.json`.', '',
        '## Thông số và giới hạn đối chiếu', '',
        'V2–V4 mới dùng NP=30, PC=PM=0.3, elite=5, nconv=8, epsilon=300 J, nmax=20;',
        'FM=0.9, eta=0.8, rho=1.23, cd=0.3, cùng đặc tính UAV trong Bảng 5.1.',
        'V1 giữ thông số repo đã chạy: elite=4, nconv=5, epsilon=100 J, nmax=15;',
        'cd thay đổi theo UAV. Vì vậy các dòng V1 là kết quả tham khảo được tái sử dụng,',
        'không phải thí nghiệm dùng đầy đủ cấu hình Chương 5.', '',
        'Giữ nguyên 40 vị trí, ma trận đường bay, nhiệm vụ và deadline trong repo.',
        'Luận văn mô tả deadline simple trong 0–3 giờ nhưng dữ liệu repo có giá trị tới 4.045 giờ;',
        'luận văn cũng liệt kê khối lượng 4 kg nhưng repo chỉ tạo 0.5, 1, 2, 3 kg.',
        'Không tự tạo lại dữ liệu ngẫu nhiên không được tài liệu công bố.',
        'Code đã sửa so với repo gốc; lần này sửa thêm kiểm tra nhiệm vụ không khả thi khi',
        'chèn sạc cuối, và kiểm tra lại deadline sau khi chèn sạc. Vì vậy đây là chạy bổ sung',
        'theo bố cục/tham số thí nghiệm, không phải khẳng định tái lập chính xác số liệu luận văn.', '',
        'Seed ban đầu 42 được đặt một lần trước mỗi scenario; 20 lượt dùng chuỗi ngẫu nhiên tiếp nối.',
        'Dùng độ lệch chuẩn mẫu. Thống kê chất lượng chỉ tính trên nghiệm hợp lệ được tìm thấy;',
        'số nghiệm / số lượt chạy được báo riêng. Không biến trường hợp không có nghiệm thành năng lượng 0.', '',
        '## Bảng 5.2 — Simple scenario', '',
        '| Phiên bản | Nguồn | Nghiệm | J chạy (MJ) | J luận văn (MJ) | Đúng hạn | Vòng lặp | CPU (s) | Lịch trình |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|',
    ]
    for v in ['V1', 'V2', 'V3', 'V4']:
        e = entries[f'simple/{v}']; m=e['metrics']; ref=e['reference']
        lines.append(f"| {v} | {'Cũ, giữ lại' if e['reused'] else 'Bổ sung'} | {e['solutions']}/1 | "
                     f"{m['score']['mean']:.6f} | {ref[0]:.2f} | {m['on_time']['mean']:.3f} | "
                     f"{m['iterations']['mean']:.0f} | {m['cpu']['mean']:.3f} | {e.get('routes')} |")
    for scenario, number in [('A', '5.3'), ('B', '5.4')]:
        lines.extend(['', f'## Bảng {number} — Complex scenario {scenario}', '',
                      '| Phiên bản | Nghiệm | E chạy (MJ), μ ± σ | E luận văn (MJ), μ ± σ | Đúng hạn chạy | Đúng hạn luận văn |',
                      '|---|---:|---|---|---|---|'])
        for v in ['V1', 'V2', 'V3', 'V4']:
            e=entries[f'{scenario}/{v}'];m=e['metrics'];ref=e['reference']
            reference_energy=fmt({'mean':ref['energy'][0], 'stdev':ref['energy'][1]}) if ref else 'Không có nghiệm'
            rp=fmt({'mean':ref['on_time'][0], 'stdev':ref['on_time'][1]}) if ref else 'Không có nghiệm'
            lines.append(f"| {v}{' (cũ)' if e['reused'] else ''} | {e['solutions']}/20 | {fmt(m['energy'])} | {reference_energy} | {fmt(m['on_time'])} | {rp} |")
        lines.extend(['', '| Phiên bản | Trạm khác nhau, μ ± σ | Lượt ghé sạc, μ ± σ | Vòng lặp, μ ± σ | CPU/lượt (s), μ ± σ | Wall/lượt (s), μ ± σ | Wall toàn chiến dịch (s) |',
                      '|---|---|---|---|---|---|---:|'])
        for v in ['V1', 'V2', 'V3', 'V4']:
            e=entries[f'{scenario}/{v}'];m=e['metrics']
            lines.append(f"| {v} | {fmt(m['unique_hubs'],2)} | {fmt(m['charging_visits'],2)} | {fmt(m['iterations'],2)} | {fmt(m['cpu'],2)} | {fmt(m['wall'],2)} | {e['campaign_wall_s']:.2f} |")
        lines.extend(['', 'Các giá trị nchar, ni, tTOT trong luận văn:', '',
                      '| Phiên bản | nchar luận văn | ni luận văn | tTOT luận văn (s) |',
                      '|---|---|---|---|'])
        for v in ['V1', 'V2', 'V3', 'V4']:
            ref=REFERENCE[scenario][v]
            values=[fmt({'mean':ref[k][0],'stdev':ref[k][1]},2) for k in ['hubs','iterations','cpu']] if ref else ['Không có nghiệm']*3
            lines.append(f"| {v} | {' | '.join(values)} |")
    lines.extend(['', '## Hình 5.1–5.3', '',
                  '- Môi trường simple: [Figure_5_1_environment.png](V2/Figure_5_1_environment.png).',
                  '- Lịch trình simple V2: [simple_figure_2.png](V2/simple_figure_2.png).',
                  '- Hội tụ simple V2: [simple_figure_1.png](V2/simple_figure_1.png).', '',
                  '## Diễn giải', '',
                  'V1 và V3 ở A không tìm được nghiệm; đây không phải chứng minh bài toán vô nghiệm.',
                  'V2/V4 cho phép trễ deadline; tỷ lệ đúng hạn dưới 1 vẫn hợp lệ theo chế độ mềm.',
                  'Tổng năng lượng E và score J được báo riêng: khi deadline mềm, J=E/p_onTime.',
                  'nchar trong luận văn ghi 4 ± 0, nhưng không giải thích đủ rõ lượt ghé hay số trạm khác nhau;',
                  'báo cáo này cung cấp cả hai đại lượng để tránh đánh đồng.',
                  'Runtime không so trực tiếp với luận văn do phần cứng, phiên bản thư viện và cache khác nhau.',
                  'Số vòng lặp hiện tại đếm vòng thực hiện; hình hội tụ bắt đầu từ chỉ số 0.', '',
                  'Mỗi nghiệm tìm được đã kiểm tra độc lập về phân công, tải trọng, pin, vận tốc, deadline theo chế độ và score.',
                  'Chưa có chứng nhận tối ưu toàn cục. Các đường thẳng trong hình minh họa chỉ biểu diễn kết nối nhiệm vụ,',
                  'không phải đường bay risk-aware thực tế trong ma trận.', '',
                  '## File và chạy tiếp', '',
                  'V1: các JSON/log cũ trong `../`. V2–V4: từng JSON/log trong các thư mục `V2`, `V3`, `V4`.',
                  '`comparison.json` lưu tất cả thống kê và số liệu đối chiếu; `regression-new-modes.log` lưu 3 kiểm tra mới.',
                  '`source-fixes.patch` lưu thay đổi code so với commit gốc; `docker-image.json` lưu thông tin image.',
                  'Chạy `./run-chapter5.ps1 -SkipBuild` từ repo: tự bỏ qua các trường hợp đã hoàn tất, không chạy lại V1.'])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'comparison.json').write_text(json.dumps(entries,indent=2,ensure_ascii=False),encoding='utf-8')
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:{'runs':v['runs'],'solutions':v['solutions'],'energy':v['metrics']['energy'],
                          'on_time':v['metrics']['on_time']} for k,v in entries.items()},indent=2))


if __name__ == '__main__':
    main()
