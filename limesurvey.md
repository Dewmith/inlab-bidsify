La structure de données BIDS (Brain Imaging Data Structure) tend à devenir le standard d'organisation de données dans les neurosciences. Si au depart BIDS est axé IRM, son succès a amené les autres techniques de neuro-imagerie à adopter le meme standard mais avec des spécifications par technique. ce sont les "extension BIDS". Nous utiliserons ici l'extension BIDS-EEG.

BIDS standardise :
une arborescence
les noms de fichiers
les metadonnées associées

Des outils permettent de generer automatiquement l'arborescence des fichiers correctement nommés et de recuperer certaines metadonnées à partir des données.
Mais certaines metadonnées ne sont pas recuperable automatiquement.

Le but de ce formulaire est de collecter ces métadonnées "manquantes".




readme

taskname (description)

manufacturer

software (version)

participant.json

powerline frequency

eegground

eeg reference


