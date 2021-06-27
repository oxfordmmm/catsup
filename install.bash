set -x
set -e

# go to home directory
cd

# install conda
wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda
./miniconda/bin/conda init bash

# clone catsup
git clone https://github.com/oxfordmmm/catsup

cd catsup

# install conda environment
../miniconda/bin/conda env create -f environment.yml

# download minikraken2 database into catsup/
wget https://objectstorage.uk-london-1.oraclecloud.com/n/lrbvkel2wjot/b/sp3_deps/o/minikraken2_v2_8GB_201904.tgz --content-disposition

# extract minikraken2 database
tar xf minikraken2_v2_8GB_201904.tgz

cp config.install-template.json config.json
sed -i "s,BASE_DIR,$HOME,g" config.json
