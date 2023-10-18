function [roi_mask, v_label, e_label] = define_roi(sub_name, varargin)

p = inputParser;

% Stimulus: 0 - 1.5 deg; 1.5 - 7 deg; 7 - 12.5 deg

% Area - Index Correspondence
% {1:  'V1',   2: 'V2',  3: 'V3',  4: 'hV4',  5: 'VO1', 6:  'VO2',  
% 7: 'LO1', 8: 'LO2', 9: 'TO1', 10: 'TO2', 11: 'V3b', 12: 'V3a'}

% Default ROI: V1 - V3 area, foeval - 7.5 degree eccentricity
p.addParameter('areaIndex', [1, 2, 3]);
p.addParameter('eccLo', 1.0, @(x)(isnumeric(x) && numel(x) == 1));
p.addParameter('eccHi', 7.0, @(x)(isnumeric(x) && numel(x) == 1));

parse(p, varargin{:});
areaIndex = p.Results.areaIndex;
eccLo = p.Results.eccLo;
eccHi = p.Results.eccHi;

[eccen, varea, ~] = load_map(sub_name);
roi_mask = boolean(zeros(size(varea)));

% select visual area
for idx = areaIndex
    roi_mask = roi_mask | varea == idx;
    fprintf('V%d ', idx)
end
fprintf('# of Voxel: %d \n', sum(roi_mask));
nVoxel = sum(roi_mask);

% apply eccentricity map
roi_mask  = roi_mask & (eccen > eccLo) & (eccen <= eccHi);
fprintf('Eccen mask: %d / %d selected \n', sum(roi_mask), nVoxel);

% visual area and ecc label
v_label = varea(roi_mask);
e_label = eccen(roi_mask);

end
