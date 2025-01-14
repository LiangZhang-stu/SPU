import os
import time
import yaml
import train
import predict
from picksamples import PickSamples

def checkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

pace_percent = [0.5, 1.0/18, 1.0/18, 1.0/18, 1.0/18, 1.0/18, 1.0/18, 1.0/18, 1.0/18, 1.0/18]

config = {
    'exp': '1',
    'alpha': 2,
    'threshold': -3.0,
    'capped': False,
    'lr': 0.00002,
    'batchsize': 32
}

alpha=[config['alpha'] for i in range(10)]

Exp = config['exp']

base_weights = '/root/new/models/VGG_FACE.t7'
checkpointsPath = './checkpoints/Exp{}/'.format(Exp)

dataset_ = 'MORPH'
max_step = 40000
train_dict = {
    'num_trees': 5, 'tree_depth': 6, 'num_classes': 1, 'dataset': dataset_,
    'num_batchs_update_forest': 50, 'iterations_update_forest': 20, 'exp': Exp,
    'train_txt': '/root/new/dataset/morph/txt-train/{}-train.txt'.format(dataset_), 
    'test_txt': '/root/new/dataset/morph/txt-train/{}-test.txt'.format(dataset_),
    'img_dir': "/root/new/dataset/morph/images/",
    'pretrain_model': (base_weights, 0, dataset_, max_step),
    'lr': config['lr'], 'max_step': max_step, 'batch_size': config['batchsize'], 'pace': 0,
    'checkpoint': checkpointsPath,
    'tensorboard':'./Exp{}/output/tensorboard/'.format(Exp),
    'MAE_savepath': './Exp{}/output/mae/'.format(Exp)
}
checkdir(train_dict['checkpoint'])
checkdir(train_dict['tensorboard'])
checkdir(train_dict['MAE_savepath'])
with open('./Exp{}/config.yaml'.format(config['exp']), 'w') as f:
        f.write(yaml.dump(config))

picksamples = PickSamples(exp=Exp, percent=pace_percent, pace=0, alpha=alpha, ent_threshold=config['threshold'],
    diff_threshold=1000, ent_pick_per=0, random_pick=False, soft=True,  soft_percent=1.0, 
    train_txt0=train_dict['train_txt'],
    img_dir=train_dict['img_dir'])

for pace in range(0, 1+len(pace_percent)):
    print('Pace %d' % pace)
    if pace == len(pace_percent):
        left_txt, pick_txt = picksamples.pick(pace=pace, capped=config['capped'])
    else:
        left_txt, pick_txt = picksamples.pick(pace=pace, capped=False)
    print('left_txt: %s' % left_txt)
    print('pick_txt: %s' % pick_txt)
    train_dict['pace'] = pace
    train_dict['tensorboard'] = './Exp{}/output/tensorboard/pace{}'.format(Exp, pace)
    checkdir(train_dict['tensorboard'])
    train_dict['tb_comment'] = 'pace' + str(pace)
    if pace == 0:
        train_dict['train_txt'] = left_txt

        train_dict['pretrain_model'] = (base_weights, 0, dataset_, max_step)
    elif pace == 1:
        train_dict['train_txt'] = pick_txt
        train_dict['pretrain_model'] = (base_weights, 0, dataset_, max_step)
    else:
        train_dict['train_txt'] = pick_txt
        train_dict['pretrain_model'] = (checkpointsPath, pace-1, dataset_, 100)   
    if pace > 0 and pace < len(pace_percent):
        train_dict['max_step'] = 30000
    else:
        train_dict['max_step'] = max_step
    print(train_dict)
    # train
    train.train(train_dict)

    # predict on train set to pick samples for each pace
    para_dict = {}
    para_dict['pretrain_model'] = (checkpointsPath, pace, dataset_, 100)
    para_dict['train_txt'] = train_dict['train_txt']
    para_dict['img_dir'] = train_dict['img_dir']
    para_dict['lr'] = train_dict['lr']
    para_dict['num_trees'] = train_dict['num_trees']
    para_dict['tree_depth'] = train_dict['tree_depth']
    para_dict['pace'] = pace
    para_dict['num_classes'] = train_dict['num_classes']

    # predict on pick set
    para_dict['test_txt'] = './Exp{}/images/Pick-{}.txt'.format(Exp, pace)
    para_dict['predict_txt'] = './Exp{}/Pred/PredOnPickset-{}.txt'.format(Exp, pace)
    predict.Predict(para_dict)

    # predict on left set
    para_dict['test_txt'] = './Exp{}/images/Left-{}.txt'.format(Exp, pace)
    para_dict['predict_txt'] = './Exp{}/Pred/PredOnLeftset-{}.txt'.format(Exp, pace)
    predict.Predict(para_dict)

    # predict on test set
    para_dict['test_txt'] = train_dict['test_txt']
    para_dict['predict_txt'] = './Exp{}/Pred/PredOnTestset-{}.txt'.format(Exp, pace)
    predict.Predict(para_dict)
