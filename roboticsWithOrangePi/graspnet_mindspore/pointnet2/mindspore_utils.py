# Copyright (c) Facebook, Inc. and its affiliates.
# 
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

''' Modified based on Ref: https://github.com/erikwijmans/Pointnet2_PyTorch '''
import mindspore as ms
import mindspore.nn as nn
import mindspore.ops.functional as F
from mindspore.common.initializer import HeNormal, initializer 
from mindspore.common.parameter import Parameter
from typing import List, Tuple

class SharedMLP(nn.SequentialCell):

    def __init__(
            self,
            args: List[int],
            *,
            bn: bool = False,
            activation=nn.ReLU(),
            preact: bool = False,
            first: bool = False
    ):
        super().__init__()

        for i in range(len(args) - 1):
            self.append(
                Conv2d(
                    args[i],
                    args[i + 1],
                    bn=(not first or not preact or (i != 0)) and bn,
                    activation=activation
                    if (not first or not preact or (i != 0)) else None,
                    preact=preact
                )
            )


class _BNBase(nn.SequentialCell):

    def __init__(self, in_size, batch_norm=None):
        super().__init__()
        self.append(batch_norm(in_size))


# class BatchNorm1d(_BNBase):

#     def __init__(self, in_size: int, *, name: str = ""):
#         super().__init__(in_size, batch_norm=nn.BatchNorm1d, name=name)


class BatchNorm2d(_BNBase):

    def __init__(self, in_size: int):
        super().__init__(in_size, batch_norm=nn.BatchNorm2d)


# class BatchNorm3d(_BNBase):

#     def __init__(self, in_size: int, name: str = ""):
#         super().__init__(in_size, batch_norm=nn.BatchNorm3d, name=name)


class _ConvBase(nn.SequentialCell):

    def __init__(
            self,
            in_size,
            out_size,
            kernel_size,
            stride,
            padding,
            activation,
            bn,
            init,
            conv=None,
            batch_norm=None,
            bias=True,
            preact=False
    ):
        super().__init__()

        bias = bias and (not bn)
        if bias:
            conv_unit = conv(
                in_size,
                out_size,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                has_bias=bias,
                bias_init=Parameter(
                initializer('zero',[1])),
                weight_init=init
            )
        else:
            conv_unit = conv(
                in_size,
                out_size,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                has_bias=bias
            )

        if bn:
            if not preact:
                bn_unit = batch_norm(out_size)
            else:
                bn_unit = batch_norm(in_size)

        if preact:
            if bn:
                self.append( bn_unit)

            if activation is not None:
                self.append(activation)

        self.append( conv_unit)

        if not preact:
            if bn:
                self.append( bn_unit)

            if activation is not None:
                self.append(activation)


# class Conv1d(_ConvBase):

#     def __init__(
#             self,
#             in_size: int,
#             out_size: int,
#             *,
#             kernel_size: int = 1,
#             stride: int = 1,
#             padding: int = 0,
#             activation=nn.ReLU(inplace=True),
#             bn: bool = False,
#             init=nn.init.kaiming_normal_,
#             bias: bool = True,
#             preact: bool = False,
#             name: str = ""
#     ):
#         super().__init__(
#             in_size,
#             out_size,
#             kernel_size,
#             stride,
#             padding,
#             activation,
#             bn,
#             init,
#             conv=nn.Conv1d,
#             batch_norm=BatchNorm1d,
#             bias=bias,
#             preact=preact,
#             name=name
#         )


class Conv2d(_ConvBase):

    def __init__(
            self,
            in_size: int,
            out_size: int,
            *,
            kernel_size: Tuple[int, int] = (1, 1),
            stride: Tuple[int, int] = (1, 1),
            padding: int = 0,
            activation=nn.ReLU(),
            bn: bool = False,
            init=HeNormal(),
            bias: bool = True,
            preact: bool = False
    ):
        super().__init__(
            in_size,
            out_size,
            kernel_size,
            stride,
            padding,
            activation,
            bn,
            init,
            conv=nn.Conv2d,
            batch_norm=BatchNorm2d,
            bias=bias,
            preact=preact
        )


# class Conv3d(_ConvBase):

#     def __init__(
#             self,
#             in_size: int,
#             out_size: int,
#             *,
#             kernel_size: Tuple[int, int, int] = (1, 1, 1),
#             stride: Tuple[int, int, int] = (1, 1, 1),
#             padding: Tuple[int, int, int] = (0, 0, 0),
#             activation=nn.ReLU(inplace=True),
#             bn: bool = False,
#             init=nn.init.kaiming_normal_,
#             bias: bool = True,
#             preact: bool = False,
#             name: str = ""
#     ):
#         super().__init__(
#             in_size,
#             out_size,
#             kernel_size,
#             stride,
#             padding,
#             activation,
#             bn,
#             init,
#             conv=nn.Conv3d,
#             batch_norm=BatchNorm3d,
#             bias=bias,
#             preact=preact,
#             name=name
#         )


# class FC(nn.Sequential):

#     def __init__(
#             self,
#             in_size: int,
#             out_size: int,
#             *,
#             activation=nn.ReLU(inplace=True),
#             bn: bool = False,
#             init=None,
#             preact: bool = False,
#             name: str = ""
#     ):
#         super().__init__()

#         fc = nn.Linear(in_size, out_size, bias=not bn)
#         if init is not None:
#             init(fc.weight)
#         if not bn:
#             nn.init.constant_(fc.bias, 0)

#         if preact:
#             if bn:
#                 self.append(name + 'bn', BatchNorm1d(in_size))

#             if activation is not None:
#                 self.append(name + 'activation', activation)

#         self.append(name + 'fc', fc)

#         if not preact:
#             if bn:
#                 self.append(name + 'bn', BatchNorm1d(out_size))

#             if activation is not None:
#                 self.append(name + 'activation', activation)

# def set_bn_momentum_default(bn_momentum):

#     def fn(m):
#         if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)):
#             m.momentum = bn_momentum

#     return fn


# class BNMomentumScheduler(object):

#     def __init__(
#             self, model, bn_lambda, last_epoch=-1,
#             setter=set_bn_momentum_default
#     ):
#         if not isinstance(model, nn.Module):
#             raise RuntimeError(
#                 "Class '{}' is not a PyTorch nn Module".format(
#                     type(model).__name__
#                 )
#             )

#         self.model = model
#         self.setter = setter
#         self.lmbd = bn_lambda

#         self.step(last_epoch + 1)
#         self.last_epoch = last_epoch

#     def step(self, epoch=None):
#         if epoch is None:
#             epoch = self.last_epoch + 1

#         self.last_epoch = epoch
#         self.model.apply(self.setter(self.lmbd(epoch)))


