import json

with open('notebooks/training_log_v2.json', encoding='utf-8') as f:
    log = json.load(f)

train_loss = [(e['step'], e['loss']) for e in log if 'loss' in e and 'eval_loss' not in e]
eval_loss  = [(e['step'], e['eval_loss']) for e in log if 'eval_loss' in e]
final      = [e for e in log if 'train_loss' in e]

print(f'Train steps       : {len(train_loss)}')
print(f'Eval checkpoints  : {len(eval_loss)}')
print(f'Initial train loss: {train_loss[0][1]:.4f}')
print(f'Final train loss  : {train_loss[-1][1]:.4f}')
print(f'Best eval loss    : {min(v for _, v in eval_loss):.4f}')
if final:
    e = final[0]
    print(f'Total steps       : {e["step"]}')
    print(f'Avg train loss    : {e["train_loss"]:.4f}')
    print(f'Runtime           : {e["train_runtime"]/3600:.2f} hours')
