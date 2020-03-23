"""
For external use as part of nbdt package. This is a model that
runs inference as an NBDT. Note these make no assumption about the
underlying neural network other than it (1) is a classification model and
(2) returns logits.
"""

import torch.nn as nn
from nbdt.utils import (
    dataset_to_default_path_graph,
    dataset_to_default_path_wnids,
    hierarchy_to_path_graph)
from nbdt.models.utils import load_state_dict_from_arch_dataset
from nbdt.data.custom import dataset_to_dummy_classes
from nbdt.analysis import SoftEmbeddedDecisionRules, HardEmbeddedDecisionRules


model_urls = {
    ('ResNet18', 'CIFAR10'): ''
}


class NBDT(nn.Module):

    def __init__(self,
            dataset,
            model,
            arch=None,
            path_graph=None,
            path_wnids=None,
            classes=None,
            hierarchy=None,
            pretrained=None,
            **kwargs):
        super().__init__()

        if dataset and hierarchy and not path_graph:
            path_graph = hierarchy_to_path_graph(dataset, hierarchy)
        if dataset and not path_graph:
            path_graph = dataset_to_default_path_graph(dataset)
        if dataset and not path_wnids:
            path_wnids = dataset_to_default_path_wnids(dataset)
        if dataset and not classes:
            classes = dataset_to_dummy_classes(dataset)
        if pretrained and not arch:
            raise UserWarning(
                'To load a pretrained NBDT, you need to specify the `arch`. '
                '`arch` is the name of the architecture. e.g., ResNet18')
        if isinstance(model, str):
            raise NotImplementedError('Model must be nn.Module')

        self.init(dataset, model, path_graph, path_wnids, classes,
            arch=arch, pretrained=pretrained, **kwargs)

    def init(self,
            dataset,
            model,
            path_graph,
            path_wnids,
            classes,
            arch=None,
            pretrained=False,
            Rules=HardEmbeddedDecisionRules):
        """
        Extra init method makes clear which arguments are finally necessary for
        this class to function. The constructor for this class may generate
        some of these required arguments if initially missing.
        """
        self.rules = Rules(path_graph, path_wnids, classes)
        self.model = model

        if pretrained:
            assert arch is not None
            state_dict = load_state_dict_from_arch_dataset(
                arch, dataset, model_urls, pretrained=True)
            if 'net' in state_dict:
                state_dict = state_dict['net']
            self.load_state_dict(state_dict)

    def load_state_dict(self, state_dict, **kwargs):
        return self.model.load_state_dict(state_dict, **kwargs)

    def state_dict(self):
        return self.model.state_dict()

    def forward(self, x):
        x = self.model(x)
        x = self.rules.forward(x)
        return x


class HardNBDT(NBDT):

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'Rules': HardEmbeddedDecisionRules
        })
        super().__init__(*args, **kwargs)


class SoftNBDT(NBDT):

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'Rules': SoftEmbeddedDecisionRules
        })
        super().__init__(*args, **kwargs)