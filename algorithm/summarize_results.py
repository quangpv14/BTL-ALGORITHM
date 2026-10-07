"""Generate a compact report after all three scenario campaigns have completed."""
import json
from pathlib import Path
import statistics

output = Path('results')
reports = {name: json.loads((output / f'{name}.json').read_text(encoding='utf-8'))
           for name in ['simple', 'A', 'B']}
if any(report.get('status') != 'completed' for report in reports.values()):
    raise SystemExit('All three scenario campaigns must complete before summarizing.')
lines = [
    '# Kết quả chạy repo UAV bằng Docker', '',
    'Commit gốc: `a85bec122b8dfe7324730e1f2d12448303f17be5`.',
    'Kết quả bên dưới dùng phiên bản đã sửa, dữ liệu và tham số GA mặc định của project.',
    'Python 3.11; NumPy 1.26.4; SciPy 1.11.4; Matplotlib 3.8.4. Seed ban đầu mỗi scenario: 42.',
    'Deadline bắt buộc; chèn sạc trong quá trình đánh giá; NP=30; PC=PM=0.3; MAX_ITER=15;',
    'ALPHA=0, BETA=1. Hai scenario phức tạp chạy 20 lượt Monte Carlo như script gốc.', '',
    '| Scenario | UAV / nhiệm vụ / trạm sạc | Số lượt | Có nghiệm | Nghiệm hợp lệ | Tổng thời gian (s) | Năng lượng trung bình (MJ) |',
    '|---|---|---:|---:|---:|---:|---:|',
]
summary = {}
for name, report in reports.items():
    runs = report['runs']
    found = [run for run in runs if run['solution_found']]
    valid = [run for run in found if run['validation']['valid']]
    energies = [run['validation']['energy_j'] / 1e6 for run in valid]
    first = runs[0]
    mean = f'{statistics.mean(energies):.6f}' if energies else 'Không có nghiệm'
    lines.append(f"| {name} | {first['uavs']} / {first['tasks']} / {first['charging_points']} | "
                 f"{len(runs)} | {len(found)} | {len(valid)} | {report['wall_time_s']:.2f} | {mean} |")
    summary[name] = {'runs': len(runs), 'solutions': len(found), 'valid_solutions': len(valid),
                     'wall_time_s': report['wall_time_s'],
                     'energy_mean_mj': statistics.mean(energies) if energies else None,
                     'energy_min_mj': min(energies) if energies else None,
                     'energy_max_mj': max(energies) if energies else None,
                     'energy_stdev_mj': statistics.stdev(energies) if len(energies) > 1 else None}
lines.extend(['', '## Ý nghĩa kết quả', '',
              '- Scenario A: không tìm được nghiệm trong 20 lần chạy. Đây không phải chứng minh bài toán vô nghiệm.',
              '- Các nghiệm được kiểm tra độc lập về đủ/đúng nhiệm vụ, tải trọng, vận tốc, pin, deadline và score.',
              '- Năng lượng được tính lại theo mô hình của repo từ khoảng cách và vận tốc suy ra từ thời gian từng bước.',
              '- Chưa có chứng nhận tối ưu toàn cục hoặc xác minh bộ lập đường bay risk-aware gốc.',
              '- Thời gian đo là wall time trong môi trường Docker của máy này; không dùng để so trực tiếp với paper.', '',
              '## Lỗi bản gốc và thay đổi', '',
              'Bản gốc lỗi ở cả ba scenario: simple đọc `sol.fun[0]` trong khi SciPy trả scalar;',
              'A/B import module `constant` không tồn tại. Xem log và JSON trong `baseline/`.',
              'Các lỗi cache, mutation, trạng thái thời gian, UAV nhàn rỗi và thống kê cũng đã được sửa.',
              'Chi tiết ở `../DOCKER_RUN.md`; patch so với commit gốc ở `source-fixes.patch`.',
              'Sáu kiểm tra hồi quy đã đạt; log ở `regression-tests.log`.', '',
              '## Chi tiết kết quả', ''])
for name, report in reports.items():
    lines.append(f'- `{name}.json`: từng lượt chạy và từng bước hành trình; `{name}.log`: toàn bộ log.')
lines.extend(['- `inputs.json`: thông tin dữ liệu; `summary.json`: thống kê tổng hợp.',
              '- `simple_figure_1.png`: đồ thị hội tụ; `simple_figure_2.png`: sơ đồ lịch trình.', '',
              'Chạy lại từ thư mục repo bằng PowerShell: `./run-docker.ps1`.',
              'Chạy riêng: `./run-docker.ps1 -Scenario B -SkipBuild`.'])
(output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
(output / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
