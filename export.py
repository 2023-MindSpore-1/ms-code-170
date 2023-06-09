# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""export MINDIR file."""
import argparse
import numpy as np
import mindspore.nn as nn
import mindspore.ops as ops
from mindspore import Tensor, context, load_checkpoint, load_param_into_net, export
from src.deeplab_v3plus import DeepLabV3Plus

context.set_context(mode=context.GRAPH_MODE, device_target='Ascend')

class BuildEvalNetwork(nn.Cell):
    """BuildEvalNetwork"""

    def __init__(self, net, input_format="NCHW"):
        super(BuildEvalNetwork, self).__init__()
        self.network = net
        self.softmax = nn.Softmax(axis=1)
        self.transpose = ops.Transpose()
        self.format = input_format

    def construct(self, x):
        if self.format == "NHWC":
            x = self.transpose(x, (0, 3, 1, 2))
        output = self.network(x)
        output = self.softmax(output)
        return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='checkpoint export')
    parser.add_argument('--checkpoint', type=str, default='', help='checkpoint of deeplabv3+ (Default: None)')
    parser.add_argument('--filename', type=str, default='deeplabv3plus16.mindir', help='filename of model')
    parser.add_argument('--model', type=str, default='DeepLabV3plus_s16',
                        choices=['DeepLabV3plus_s16', 'DeepLabV3plus_s8'],
                        help='Select model structure (Default: DeepLabV3plus_s16)')
    parser.add_argument('--num_classes', type=int, default=21, help='the number of classes (Default: 21)')
    args = parser.parse_args()

    if args.model == 'DeepLabV3plus_s16':
        network = DeepLabV3Plus('eval', args.num_classes, 16, False)
    else:
        network = DeepLabV3Plus('eval', args.num_classes, 8, False)
    network = BuildEvalNetwork(network, "NCHW")
    param_dict = load_checkpoint(args.checkpoint)

    # load the parameter into net
    load_param_into_net(network, param_dict)
    input_data = Tensor(np.ones([8, 3, 513, 513]).astype(np.float32))
    #if deeplabv3+s8，batchsize=8，if s16，batchsize为16
    export(network, input_data, file_name=args.filename, file_format='MINDIR')
